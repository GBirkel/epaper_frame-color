#include <stdlib.h>     //exit()
#include <signal.h>     //signal()
#include <stdbool.h>
#include <time.h>
#include "lib/e-Paper/EPD_13in3e.h"
#include "lib/GUI/GUI_Paint.h"
#include "lib/GUI/GUI_BMPfile.h"
#include "lib/Config/DEV_Config.h"

int Version;

bool display_message = false;
char *message_ptr;

void Handler(int signo)
{
    //System Exit
    printf("\r\nHandler:Goto Sleep mode\r\n");
    DEV_ModuleExit();
    exit(0);
}

int main(int argc, char *argv[])
{
    // Exception handling:ctrl + c
    signal(SIGINT, Handler);

	if (argc < 2) {
		printf("Please provide a path to a BMP image!\r\n");
		exit(1);
    }

	if (argc == 3) {
        display_message = true;
        message_ptr = argv[4];
    }

    char *Pathname = argv[1];

    printf("epd: ModuleInit\r\n");
    DEV_ModuleInit();
    DEV_Delay_ms(500);

    printf("epd: EPD_13IN3E_Init\r\n");
    EPD_13IN3E_Init();
    //printf("epd: EPD_13IN3E_Clear\r\n");
    //EPD_13IN3E_Clear(EPD_13IN3E_WHITE);
    //DEV_Delay_ms(500);

    printf("epd: Allocating image memory\r\n");
    //Create a new image cache
    UBYTE *Image;
    /* you have to edit the startup_stm32fxxx.s file and set a big enough heap size */
    UDOUBLE Imagesize = ((EPD_13IN3E_WIDTH % 2 == 0)? (EPD_13IN3E_WIDTH / 2 ): (EPD_13IN3E_WIDTH / 2 + 1)) * EPD_13IN3E_HEIGHT;
    if((Image = (UBYTE *)malloc(Imagesize)) == NULL) {
        printf("Failed to apply for black memory...\r\n");
        return -1;
    }

    printf("epd: Paint_SetScale\r\n");
    Paint_NewImage(Image, EPD_13IN3E_WIDTH, EPD_13IN3E_HEIGHT, 0, WHITE);
    Paint_SetScale(6);

    // printf("show bmp------------------------\r\n");
    printf("epd: Paint_Clear\r\n");
    Paint_Clear(WHITE);   
    printf("epd: GUI_ReadBmp\r\n");
    GUI_ReadBmp(Pathname, 0, 0);
    printf("epd: Paint_DrawString_EN\r\n");
    if (display_message) {
        Paint_DrawString_EN(10, 10, message_ptr, &Font24, EPD_13IN3E_WHITE, EPD_13IN3E_BLACK);
    }
    printf("epd: EPD_13IN3E_Display\r\n");
    EPD_13IN3E_Display(Image);
    DEV_Delay_ms(1000);

    printf("epd: EPD_13IN3E_Sleep\r\n");
    EPD_13IN3E_Sleep();
    printf("epd: Freeing image memory\r\n");
    free(Image);
    Image = NULL;
    DEV_ModuleExit();
    return 0; 
}
