#!/usr/bin/python
# #-*- encoding: utf-8 -*-
#__author__ = '§Chu'

import csv
import cv2
import glob
from PIL import Image
from skimage.measure import compare_ssim as ssim
import sys
import tesserocr
import time
import xml.etree.ElementTree as ET


def load_screenshots(img_path, images):
    filenames = [img for img in glob.glob(img_path)]
    filenames.sort()
    for img in filenames:
        n = cv2.imread(img)
        images.append(n)


def image_processing(imageA, img0, lang, csv_file):
    count = 0
    img = imageA.copy()
    # prepare image quality for OCR
    img = cv2.bitwise_not(img)
    _, img_recog = cv2.threshold(img, 210, 255, cv2.THRESH_BINARY)
    _, img = cv2.threshold(img, 224, 255, cv2.THRESH_BINARY)

    #find text areas
    imgBi = cv2.bitwise_not(imageA)
    _, binary2 = cv2.threshold(imgBi, 0, 255, cv2.THRESH_BINARY)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (21, 20))
    eroded = cv2.erode(binary2, kernel, iterations=1)
    erodedBi = cv2.bitwise_not(eroded)
    contours2, hierarchy2 = cv2.findContours(erodedBi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # find head area for OCR text with color
    headArea = img_recog[104:204, 319:1493]
    erodedHead = cv2.erode(headArea, kernel, iterations=1)
    erodedHead = cv2.bitwise_not(erodedHead)
    contours, hierarchy = cv2.findContours(erodedHead, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for i in range(len(contours)):
        x, y, w, h = cv2.boundingRect(contours[i])
        if w < 1000:
            count += 1
            cv2.rectangle(img0, (x+319, y+104), (x+319+w, y+104+h), (0, 255, 0), 2)
            crop_img = headArea[y:y+h, x:x+w]
            cv2.imwrite('ref.png', crop_img)
            text = tesserocr.image_to_text(Image.open('ref.png'), lang)
            text = text.replace(" ", "")
            text = text.replace("\n", " ")
            csv_file.write('{}:,{},{},{},{},{}\n'.format(count, x, y, w, h, text.encode('utf-8')))

    for j in range(len(contours2)):
            cnt2 = contours2[j]
            x2, y2, w2, h2 = cv2.boundingRect(cnt2)
            if x2 > 120 and y2 > 200 and 2 < w2 and 2 < h2 < 450:
                count += 1
                cv2.rectangle(img0, (x2, y2), (x2+w2, y2+h2), (0, 255, 0), 2)
                crop_img = img_recog[y2:y2+h2, x2:x2+w2]
                cv2.imwrite('ref.png', crop_img)
                text = tesserocr.image_to_text(Image.open('ref.png'), lang)
                text = text.replace(" ", "")
                text = text.replace("\n", " ")
                csv_file.write('{}:,{},{},{},{},{}\n'.format(count, x2, y2, w2, h2, text.encode('utf-8')))
            else:
                pass


def filter_screenshots(images, ref, lang, csv_file):
    with open(csv_file, 'w') as csv_file:
        for i in range(len(images)):
            imageA = images[i]
            height, width, depth = imageA.shape
            # get chinese part of screenshots
            imageA = imageA[0:720, 0:width]
            img0 = imageA.copy()
            imageA = cv2.cvtColor(imageA, cv2.COLOR_BGR2GRAY)
            if i < (len(images) - 1):
                imageB = images[i+1]
                imageB = imageB[0:720, 0:width]
                imageB = cv2.cvtColor(imageB, cv2.COLOR_BGR2GRAY)

                # rescale iamges to realise fast difference calculation
                imgA = cv2.resize(imageA, (8, 8), interpolation=cv2.INTER_LINEAR)
                imgB = cv2.resize(imageB, (8, 8), interpolation=cv2.INTER_LINEAR)
                # compare differences between image i and image i+1
                (score, diff) = ssim(imgA, imgB, full=True)
                if ref != i:
                    image_processing(imageA, img0, lang, csv_file)
                else:
                    pass
                if score > 0.99:
                    ref = i + 1
                else:
                    ref = i

            else:
                if ref != i:
                    image_processing(imageA, img0, lang, csv_file)


def get_target_value(xml_file, target_value_file):
    with open(target_value_file, 'w') as target_value_file:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        props = root[0]
        count = 1
        for child in props:
            text = child[0]
            value = text.get('value')
            value = value.strip()
            value = value.replace("\\n", "")
            target_value_file.write('{}\n'.format(value.encode('utf-8')))
            count += 1


def get_actual_elements(imgInfoFile, actualElementFile):
    lines_seen = set()
    with open(imgInfoFile, 'r') as imgInfoFile:
        with open(actualElementFile, 'w') as actualElementFile:
            for line in imgInfoFile:
                if line not in lines_seen:
                    actualElementFile.write(line)
                    lines_seen.add(line)


def get_actual_value(actual_element_file, actual_value_file):
    actual = []
    with open(actual_element_file, 'r') as actual_element_file:
        with open(actual_value_file, 'w') as actual_value_file:
            istFile = csv.reader(actual_element_file)
            for line in istFile:
                if len(line) == 6:
                    actual.append(line[5])

            for item in actual:
                if len(item) != 0:
                    actualItem = item.strip() #remove the whitespace before & after the string
                    actual_value_file.write('{}\n'.format(actualItem))


def compare_difference(target_value_file, actual_value_file):
    with open(target_value_file, 'r') as target_value:
        with open(actual_value_file, 'r') as actual_value:
            alines = csv.reader(target_value)
            blines = csv.reader(actual_value)
            a = []
            b = []
            correct = []
            wrong = []
            countCorrect = 0
            for aline in alines:
                a.append(aline[0])
            for bline in blines:
                b.append(bline[0])
            total = len(a)

            for itema in range(len(a)):
                similarity = 0
                for itemb in range(len(b)):
                    if b[itemb] == a[itema]:
                        state = 1
                        countCorrect += 1
                        #filew.writerow(a[itema])
                        del b[itemb]
                        correct.append(a[itema])
                        break

                    else: # split itema, itemb into separate characters
                        x = a[itema].decode('utf-8')
                        tmpa = []
                        for i in range(len(x)):
                            tmpa.append(x[i].encode('utf-8'))

                        y = b[itemb].decode('utf-8')
                        tmpb = []
                        for j in range(len(y)):
                            tmpb.append(y[j].encode('utf-8'))

                        #compare similarity of characters itema and itemb
                        compare = []
                        for l in tmpa:
                            if l in tmpb:
                                compare.append(l)
                        if len(compare) == len(tmpa) and len(compare) == (len(tmpb) - 1):
                            state = 1
                            correct.append(a[itema] + '(actual text: ' + b[itemb] + ')')
                            del b[itemb]
                            break
                        else:
                            siml = len(compare)/float(len(tmpa))
                            if siml > similarity:
                                similarity = siml
                                ref_text = b[itemb]
                            state = 0
                if state == 0:
                    if similarity > 0.3:
                        wrong.append(a[itema] + '\n(similarity: ' + str(similarity) +\
                                     ', compared with actual text: ' + ref_text + ')')
                    else:
                        wrong.append(a[itema] + '\n(similarity: ' + str(similarity) + ')')

            print '\n======================================================'
            #print 'Correct:\n', '\n'.join(str(item) for item in correct)
            #print '\n-------------------------------------------'
            print 'Test cases in the xml file are not found in screenshots: \n\n', '\n'.join(str(item) for item in wrong)


def compare_difference2(target_value_file, actual_value_file):
     with open(target_value_file, 'r') as target_value:
        with open(actual_value_file, 'r') as actual_value:
            alines2 = csv.reader(target_value)
            blines2 = csv.reader(actual_value)
            a2 = []
            b2 = []
            correct2 = []
            judge2 = []
            wrong2 = []
            countCorrect2 = 0
            for aline2 in alines2:
                a2.append(aline2[0])
            for bline2 in blines2:
                b2.append(bline2[0])
            total2 = len(b2)

            for itemb2 in range(len(b2)):
                similarity = 0
                for itema2 in range(len(a2)):
                    if (b2[itemb2] == a2[itema2]):
                        state2 = 1
                        countCorrect2 += 1
                        correct2.append(b2[itemb2])
                        break
                    else: # split itema2, itemb2 into sepatate characters
                        x = a2[itema2].decode('utf-8')
                        tmpa = []
                        for i in range(len(x)):
                            tmpa.append(x[i].encode('utf-8'))

                        y = b2[itemb2].decode('utf-8')
                        tmpb = []
                        for j in range(len(y)):
                            tmpb.append(y[j].encode('utf-8'))

                        #compare similarity of characters in itema2 and itemb2
                        compare = []
                        for l in tmpb:
                            if l in tmpa:
                                compare.append(l)
                        if len(compare) == len(tmpa) and len(compare) == (len(tmpb) - 1):
                            state2 = 1
                            correct2.append(b2[itemb2] + '(target text: ' + a2[itema2] + ')')
                            break
                        else:
                            siml = len(compare)/float(len(tmpb))
                            if siml > similarity:
                                similarity = siml
                                ref_text = a2[itema2]
                            state2 = 0
                if state2 == 0:
                    if similarity >= 0.66:
                        judge2.append(b2[itemb2] + '\n(similarity: ' + str(similarity) +\
                                     ', compared with target text: ' + ref_text + ')')
                    elif similarity >= 0.4:
                        wrong2.append(b2[itemb2] + '\n(similarity: ' + str(similarity) +\
                                     ', compared with target text: ' + ref_text + ')')
                    else:
                        wrong2.append(b2[itemb2] + '\n(similarity: ' + str(similarity) + ')')
                    #x = list(set(a[itema])-set(b[itemb]))
                    #print x[0]

            accuracy2 = (countCorrect2/float(total2)) * 100.00

            print '\n======================================================'
            print 'Correct: \n'
            correct2set = set(correct2)
            for item in correct2set:
                print ("%s  found %d times" %(item, correct2.count(item)))

            print '\n======================================================'
            print 'Recognized texts from screenshots are not found in the xml file: \n'

            judge2set = set(judge2)
            for item in judge2set:
                print ("%s  found %d times" %(item, judge2.count(item)))

            wrong2set = set(wrong2)
            for item in wrong2set:
                print ("%s  found %d times" %(item, wrong2.count(item)))



def main():
    start = time.clock()
    #file_path_head = "test/"
    file_path_head = sys.argv[1]
    img_path = "%s%s" % (file_path_head,'*.png')
    images = []
    load_screenshots(img_path, images)

    #lang = 't7'
    lang = sys.argv[3]
    csv_file = "%s%s" % (file_path_head, 'output.csv')

    ref = 1
    filter_screenshots(images, ref, lang, csv_file)

    xml_file = sys.argv[2]
    #xml_file = 'T/CAR_DRIVE_SELECT_INDIVIDUAL_Evo2plus.xml'
    target_value_file = "%s%s" % (file_path_head, 'target_value.csv')
    get_target_value(xml_file, target_value_file)

    img_info_file = "%s%s" % (file_path_head, 'output.csv')
    actual_element_file = "%s%s" % (file_path_head, 'actual_element.csv')
    get_actual_elements(img_info_file, actual_element_file)

    actual_value_file = "%s%s" % (file_path_head, 'actual_value.csv')
    get_actual_value(actual_element_file, actual_value_file)

    compare_difference2(target_value_file, actual_value_file)

    compare_difference(target_value_file, actual_value_file)

    elapsed = (time.clock() - start)
    print '\nprocessing time: ' + str(elapsed) + 's'

main()

