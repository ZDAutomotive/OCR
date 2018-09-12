#include <tesseract/baseapi.h>
#include <leptonica/allheaders.h>

int main()
{
	char *outText;
	// Open input image with leptonica library
	Pix *image = pixRead("C:\\Users\\ZD\\Desktop\\tesseract-3.04.01\\testing\\ScreenShot_20170622_143601_CAR_prOn_0.png");
	tesseract::TessBaseAPI *api = new tesseract::TessBaseAPI();
	// Initialize tesseract-ocr with English, without specifying tessdata path
	if (api->Init(NULL, "t8")){
		fprintf(stderr, "Could not initialize tesseract.\n");
		exit(1);
	}
	api->SetImage(image);
	Boxa* boxes = api->GetComponentImages(tesseract::RIL_TEXTLINE, true, NULL, NULL);
	printf("found %d textline iamge components.\n", boxes->n);

	// Get OCR result
	/*for (int i = 0; i < boxes->n; i++){
        BOX* box = boxaGetBox(boxes, i, L_CLONE);
        api->SetRectangle(box->x, box->y, box->w, box->h);
        char* ocrResult = api->GetUTF8Text();
        int conf = api->MeanTextConf();
        fprintf(stdout, "Box[%d]: x=%d, y=%d, w=%d, h=%d, confidence: %d, text: %s",
            i, box->x, box->y, box->w, box->h, conf, ocrResult);
    }*/
	outText = api->GetUTF8Text();
	printf("OCR output:\n%s", outText);
	
	// Destroy used object and release memory
	api->End();
	delete [] outText;
	pixDestroy(&image);
	
	return 0;
}
