def check_html_closing_tags(html_code):
    stack = []
    i = 0
    while i < len(html_code):
        if html_code[i] == '<':
            end = html_code.find('>', i)
            if end == -1:  # 没有找到结束标记
                return "HTML 格式错误: 标签未闭合"

            tag_content = html_code[i + 1:end].strip()
            if tag_content.startswith('/'):  # 关闭标签
                tag_name = tag_content[1:].split()[0]  # 取得标签名
                if stack and stack[-1] == tag_name:
                    stack.pop()  # 匹配，弹出栈顶标签
                elif tag_name not in ['head', 'html']:  # 只在不是 head 或 html 标签时返回错误
                    return f"未正确闭合的标签: <{tag_name}>"
            else:  # 开放标签
                tag_name = tag_content.split()[0]  # 取标签名
                if tag_name not in ['head', 'html', '!DOCTYPE', 'meta']:  # 跳过<head>和<html>标签
                    if not tag_content.endswith('/'):  # 非自闭合标签
                        stack.append(tag_name)

            i = end + 1  # 更新位置到标签结束之后
        else:
            i += 1  # 如果不是标签，继续向后移动

    if stack:  # 如果栈不为空，说明有未闭合的标签
        return f"未正确闭合的标签: <{', '.join(stack)}>"

    return "所有标签闭合正确！"

# 测试函数
def test_check_html_closing_tags():
    test_cases = [
        ("<html><head><title>Test</title></head><body><h1>Hello, World!</h1></body></html>", 
         "所有标签闭合正确！"),
        ("<html><head><title>Test</head><body><h1>Hello, World!</h1></body></html>", 
         "未正确闭合的标签: <title>"),
        ("<html><head><title>Test</title></head></title><body><h1>Hello, World!</h1></body></html>", 
         "未正确闭合的标签: <title>"),
        ("<html><head><title>Test</title></head><body><img src='image.jpg' alt='Image' /></body></html>", 
         "所有标签闭合正确！"),
        ("<!DOCTYPE html><html lang='zh'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'><title>您的标题</title></head><body><p></p></body></html>",
         "所有标签闭合正确！"),
    ]
    fh = []
    for i, (input_html, expected_output) in enumerate(test_cases, 1):
        actual_output = check_html_closing_tags(input_html)
        print(f"测试案例{i}输入: {input_html}")
        print(f"测试案例{i}预期输出: {expected_output}")
        print(f"测试案例{i}实际输出: {actual_output}")
        print("--------------------------------------------------")
        if actual_output != expected_output:
            fh.append(f"测试案例{i}不符合预期输出！")
        else:
            fh.append(f"测试案例{i}符合预期输出！")
        print("\n")
    for i in fh:
        print(i)

# 调用测试函数
test_check_html_closing_tags()
