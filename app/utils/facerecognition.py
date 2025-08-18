# author 风逝

import os
import cv2
import face_recognition


def check_face(known_path, unknown_path):
    """
    用于人脸判别
    """
    picture_of_known = []  # 已知的图片文件
    known_faces_encoding = []  # 已知的图片编码

    # 加载图片
    files = file_name(known_path)
    for i in range(len(files)):
        picture_of_known.append(face_recognition.load_image_file(known_path + files[i]))

    unknown_picture = face_recognition.load_image_file(unknown_path)

    # 编码图片
    for i in range(len(picture_of_known)):
        known_face_encodings = face_recognition.face_encodings(picture_of_known[i])
        if len(known_face_encodings) > 0:
            known_faces_encoding.append(known_face_encodings[0])
    # 如果没有人脸，此处会报数组越界异常
    unknown_face_encoding = face_recognition.face_encodings(unknown_picture)
    if len(unknown_face_encoding) > 0:
        unknown_face_encoding = unknown_face_encoding[0]
        # 人脸验证的结果
        results = face_recognition.compare_faces(known_faces_encoding, unknown_face_encoding, tolerance=0.5)
        for i in range(len(results)):
            if results[i]:
                file = files[i].split(".")[0]
                print("file:" + file)
                return file
    return None


def delete_pic(path):
    """
    文件数量超过限制，删除一个文件
    :param path:
    :return:
    """
    files = os.listdir(path)
    files.sort()
    imgCount = files.__len__()
    if imgCount > 10:
        # 图片超过10个，删除一个
        os.unlink(path + files[0])


def file_name(file_dir):
    """
    遍历文件夹"
    """""
    for root, dirs, files in os.walk(file_dir):
        pass
    return files


def shape_pic(pic_path):
    """
    裁剪照片
    """
    src = cv2.imread(pic_path)
    print(pic_path)
    try:
        grey = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
    except:
        pass
    # 告诉OpenCV使用人脸识别分类器
    classfier = cv2.CascadeClassifier('E:/opencv/sources/data/haarcascades/haarcascade_frontalface_alt2.xml')
    # 人脸检测，1.2和2分别为图片缩放比例和需要检测的有效点数
    faceRects = classfier.detectMultiScale(grey, scaleFactor=1.2, minNeighbors=3, minSize=(32, 32))
    if len(faceRects) > 0:  # 大于0则检测到人脸
        for faceRect in faceRects:  # 单独框出每一张人脸
            x, y, w, h = faceRect
            image = src[y - 10:y + h + 10, x - 10:x + w + 10]
            cv2.imwrite(pic_path, image)
            return True
    return False
