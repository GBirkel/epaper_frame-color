#include "lib/Config/DEV_Config.h"
#include "main.h"
#include "lib/e-Paper/EPD_IT8951.h"
#include "lib/GUI/GUI_Paint.h"
#include "lib/GUI/GUI_BMPfile.h"
#include "lib/Config/Debug.h"

#include <math.h>

#include <stdlib.h>     //exit()
#include <signal.h>     //signal()


#include <time.h> 
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <fcntl.h>
#include <stdlib.h>

UBYTE *Refresh_Frame_Buf = NULL;
UBYTE *Panel_Area_Frame_Buf = NULL;
UBYTE *Panel_Frame_Buf = NULL;

bool Four_Byte_Align = false;

extern UBYTE isColor;

UWORD VCOM = 2510;

IT8951_Dev_Info Dev_Info = {0, 0};
UWORD Panel_Width;
UWORD Panel_Height;
UDOUBLE Init_Target_Memory_Addr;

bool display_message = false;
char *message_ptr;

int epd_mode = 0;	//0: no rotate, no mirror
					//1: no rotate, horizontal mirror, for 10.3inch
					//2: no totate, horizontal mirror, for 5.17inch
					//3: no rotate, no mirror, isColor, for 6inch color


/******************************************************************************
function: Change direction of display, Called after Paint_NewImage()
parameter:
    mode: display mode
******************************************************************************/
static void Epd_Mode(int mode)
{
	if(mode == 3) {
		Paint_SetRotate(ROTATE_0);
		Paint_SetMirroring(MIRROR_NONE);
		isColor = 1;
	}else if(mode == 2) {
		Paint_SetRotate(ROTATE_0);
		Paint_SetMirroring(MIRROR_HORIZONTAL);
	}else if(mode == 1) {
		Paint_SetRotate(ROTATE_0);
		Paint_SetMirroring(MIRROR_HORIZONTAL);
	}else {
		Paint_SetRotate(ROTATE_0);
		Paint_SetMirroring(MIRROR_NONE);
	}
}


void  Handler(int signo){
    Debug("\r\nHandler:exit\r\n");
    if(Refresh_Frame_Buf != NULL){
        free(Refresh_Frame_Buf);
        Debug("free Refresh_Frame_Buf\r\n");
        Refresh_Frame_Buf = NULL;
    }
    if(Panel_Frame_Buf != NULL){
        free(Panel_Frame_Buf);
        Debug("free Panel_Frame_Buf\r\n");
        Panel_Frame_Buf = NULL;
    }
    if(Panel_Area_Frame_Buf != NULL){
        free(Panel_Area_Frame_Buf);
        Debug("free Panel_Area_Frame_Buf\r\n");
        Panel_Area_Frame_Buf = NULL;
    }
    if(bmp_src_buf != NULL){
        free(bmp_src_buf);
        Debug("free bmp_src_buf\r\n");
        bmp_src_buf = NULL;
    }
    if(bmp_dst_buf != NULL){
        free(bmp_dst_buf);
        Debug("free bmp_dst_buf\r\n");
        bmp_dst_buf = NULL;
    }
	if(Dev_Info.Panel_W != 0){
		Debug("Going to sleep\r\n");
		EPD_IT8951_Sleep();
	}
    DEV_Module_Exit();
    exit(0);
}


int main(int argc, char *argv[])
{
    //Exception handling:ctrl + c
    signal(SIGINT, Handler);

    if (argc < 2) {
        Debug("Please input VCOM value on FPC cable!\r\n");
        Debug("Example: sudo ./epd -2.51\r\n");
        exit(1);
    }
	if (argc < 3) {
		Debug("Please input e-Paper display mode!\r\n");
		Debug("Example: sudo ./epd -2.51 0 or sudo ./epd -2.51 1\r\n");
		Debug("10.3 inch glass panel is mode 1, else is mode 0\r\n");
		Debug("If you don't know what to type in just type 0\r\n");
		exit(1);
    }
	if (argc < 4) {
		Debug("Please provide a path to a BMP image!\r\n");
		exit(1);
    }

	if (argc == 5) {
        display_message = true;
        message_ptr = argv[4];
    }

    //Init the BCM2835 Device
    if(DEV_Module_Init()!=0){
        return -1;
    }

    double temp;
    sscanf(argv[1],"%lf",&temp);
    VCOM = (UWORD)(fabs(temp)*1000);
    Debug("VCOM value:%d\r\n", VCOM);
	sscanf(argv[2],"%d",&epd_mode);
    Debug("Display mode:%d\r\n", epd_mode);
    Dev_Info = EPD_IT8951_Init(VCOM);

    //get some important info from Dev_Info structure
    Panel_Width = Dev_Info.Panel_W;
    Panel_Height = Dev_Info.Panel_H;
    Init_Target_Memory_Addr = Dev_Info.Memory_Addr_L | (Dev_Info.Memory_Addr_H << 16);
    char* LUT_Version = (char*)Dev_Info.LUT_Version;
    if( strcmp(LUT_Version, "M641") == 0 ){
        //6inch e-Paper HAT(800,600), 6inch HD e-Paper HAT(1448,1072), 6inch HD touch e-Paper HAT(1448,1072)
        A2_Mode = 4;
        Four_Byte_Align = true;
    }else if( strcmp(LUT_Version, "M841_TFAB512") == 0 ){
        //Another firmware version for 6inch HD e-Paper HAT(1448,1072), 6inch HD touch e-Paper HAT(1448,1072)
        A2_Mode = 6;
        Four_Byte_Align = true;
    }else if( strcmp(LUT_Version, "M841") == 0 ){
        //9.7inch e-Paper HAT(1200,825)
        A2_Mode = 6;
    }else if( strcmp(LUT_Version, "M841_TFA2812") == 0 ){
        //7.8inch e-Paper HAT(1872,1404)
        A2_Mode = 6;
    }else if( strcmp(LUT_Version, "M841_TFA5210") == 0 ){
        //10.3inch e-Paper HAT(1872,1404)
        A2_Mode = 6;
    }else{
        //default set to 6 as A2 Mode
        A2_Mode = 6;
    }
    Debug("A2 Mode:%d\r\n", A2_Mode);

	EPD_IT8951_Clear_Refresh(Dev_Info, Init_Target_Memory_Addr, GC16_Mode);

    // Begin display BMP operation

    UBYTE BitsPerPixel = BitsPerPixel_4;
    char *Pathname = argv[3];

    UWORD WIDTH;

    if(Four_Byte_Align == true){
        WIDTH  = Panel_Width - (Panel_Width % 32);
    }else{
        WIDTH = Panel_Width;
    }
    UWORD HEIGHT = Panel_Height;

    UDOUBLE Imagesize;

    Imagesize = ((WIDTH * BitsPerPixel % 8 == 0)? (WIDTH * BitsPerPixel / 8 ): (WIDTH * BitsPerPixel / 8 + 1)) * HEIGHT;
    if((Refresh_Frame_Buf = (UBYTE *)malloc(Imagesize)) == NULL) {
        Debug("Failed to apply for framebuffer memory...\r\n");
        return -1;
    }

    Paint_NewImage(Refresh_Frame_Buf, WIDTH, HEIGHT, 0, BLACK);
    Paint_SelectImage(Refresh_Frame_Buf);
	Epd_Mode(epd_mode);
    Paint_SetBitsPerPixel(BitsPerPixel);
    Paint_Clear(WHITE);

	GUI_ReadBmp(Pathname, 0, 0);

    switch(BitsPerPixel){
        case BitsPerPixel_8:{
//            Paint_DrawString_EN(10, 10, "8 bits per pixel 16 grayscale", &Font24, 0xF0, 0x00);
            EPD_IT8951_8bp_Refresh(Refresh_Frame_Buf, 0, 0, WIDTH,  HEIGHT, false, Init_Target_Memory_Addr);
            break;
        }
        case BitsPerPixel_4:{
            if (display_message) {
    			Paint_DrawString_EN(10, 10, message_ptr, &Font24, 0xF0, 0x00);
            }
            EPD_IT8951_4bp_Refresh(Refresh_Frame_Buf, 0, 0, WIDTH,  HEIGHT, false, Init_Target_Memory_Addr,false);
            break;
        }
        case BitsPerPixel_2:{
//            Paint_DrawString_EN(10, 10, "2 bits per pixel 4 grayscale", &Font24, 0xC0, 0x00);
            EPD_IT8951_2bp_Refresh(Refresh_Frame_Buf, 0, 0, WIDTH,  HEIGHT, false, Init_Target_Memory_Addr,false);
            break;
        }
        case BitsPerPixel_1:{
//            Paint_DrawString_EN(10, 10, "1 bit per pixel 2 grayscale", &Font24, 0x80, 0x00);
            EPD_IT8951_1bp_Refresh(Refresh_Frame_Buf, 0, 0, WIDTH,  HEIGHT, A2_Mode, Init_Target_Memory_Addr,false);
            break;
        }
    }

    if(Refresh_Frame_Buf != NULL){
        free(Refresh_Frame_Buf);
        Refresh_Frame_Buf = NULL;
    }

    // (Brought this down to 2 seconds from 5 after testing)
    DEV_Delay_ms(2000);

    // Done with display BMP operation

    //EPD_IT8951_Standby();
    EPD_IT8951_Sleep();

    //In case RPI is transmitting image in no hold mode, which requires at most 10s
    // (Brought this down to 2 seconds from 5 after testing)
    DEV_Delay_ms(2000);

    DEV_Module_Exit();
    return 0;
}
