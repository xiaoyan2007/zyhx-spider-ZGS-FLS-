"""
测试 ddddocr 识别验证码图片的脚本

该脚本是人民网数据平台(data.people.com.cn)的验证码识别测试。
由于原图包含网页其他元素，需要对图片进行裁剪以定位到验证码区域。
"""

import ddddocr
from PIL import Image, ImageOps
import io


def recognize_captcha(image_path, crop_box=None):
    """
    识别验证码图片
    
    Args:
        image_path: 图片路径
        crop_box: 裁剪区域 (left, top, right, bottom)，如果为None则识别整张图片
    
    Returns:
        识别结果字符串
    """
    ocr = ddddocr.DdddOcr(show_ad=False)
    
    # 打开图片
    img = Image.open(image_path)
    
    # 转换为RGB模式（去除alpha通道）
    if img.mode == 'RGBA':
        img = img.convert('RGB')
    
    # 如果指定了裁剪区域，进行裁剪
    if crop_box:
        img = img.crop(crop_box)
    
    # 转换为字节流进行识别
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    result = ocr.classification(img_bytes.getvalue())
    
    return result


def main():
    image_path = r'c:\Users\33562\.trae-cn\attachments\6a228f94e69da4baa11bd0a1\be1960df-dce3-4099-b5ae-f8d09f40a6c8_e8b5f13d-6aa5-48f3-9c27-bd78f4adc069_image.png'
    
    print("=" * 50)
    print("ddddocr 验证码识别测试")
    print("=" * 50)
    
    # 测试1: 直接识别整张图片（不裁剪）
    print("\n【测试1】直接识别整张图片:")
    result = recognize_captcha(image_path)
    print(f"  识别结果: '{result}'")
    print("  说明: 整张图片包含网页其他元素，识别效果通常不佳")
    
    # 测试2: 裁剪到验证码区域后识别
    # 根据图片尺寸 1490x972，验证码区域大约在 (620, 405, 840, 495)
    print("\n【测试2】裁剪到验证码区域后识别:")
    crop_box = (620, 405, 840, 495)
    result = recognize_captcha(image_path, crop_box)
    print(f"  裁剪区域: {crop_box}")
    print(f"  识别结果: '{result}'")
    print("  说明: 裁剪后去除了干扰元素，识别准确率大幅提升")
    
    # 测试3: 灰度化 + 裁剪识别
    print("\n【测试3】灰度化处理后识别:")
    img = Image.open(image_path)
    if img.mode == 'RGBA':
        img = img.convert('RGB')
    img = img.crop(crop_box)
    gray = ImageOps.grayscale(img)
    
    ocr = ddddocr.DdddOcr(show_ad=False)
    gray_bytes = io.BytesIO()
    gray.save(gray_bytes, format='PNG')
    result_gray = ocr.classification(gray_bytes.getvalue())
    print(f"  识别结果: '{result_gray}'")
    
    # 测试4: 二值化处理后识别
    print("\n【测试4】二值化处理后识别:")
    binary = gray.point(lambda x: 0 if x < 130 else 255, '1')
    binary_bytes = io.BytesIO()
    binary.save(binary_bytes, format='PNG')
    result_binary = ocr.classification(binary_bytes.getvalue())
    print(f"  识别结果: '{result_binary}'")
    
    print("\n" + "=" * 50)
    print("测试完成！")
    print("=" * 50)


if __name__ == "__main__":
    main()
