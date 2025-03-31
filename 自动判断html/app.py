from flask import Flask, render_template, request, redirect, url_for, session
from bs4 import BeautifulSoup
import json
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 用于会话管理，请更换为安全的密钥

# 文件路径
USERS_FILE = 'users.json'
COMPLETED_QUESTIONS_FILE = 'user_completed_questions.json'


# 读取用户信息
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as file:
            return json.load(file)
    return {}


# 保存用户信息
def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as file:
        json.dump(users, file, ensure_ascii=False, indent=4)


# 读取用户已完成的问题
def load_user_completed_questions():
    if os.path.exists(COMPLETED_QUESTIONS_FILE):
        with open(COMPLETED_QUESTIONS_FILE, 'r', encoding='utf-8') as file:
            return json.load(file)
    return {}


# 保存用户已完成的问题
def save_user_completed_questions(user_completed_questions):
    with open(COMPLETED_QUESTIONS_FILE, 'w', encoding='utf-8') as file:
        json.dump(user_completed_questions, file, ensure_ascii=False, indent=4)


# 读取题目数据
def load_questions():
    with open("questions.json", "r", encoding="utf-8") as file:
        return json.load(file)


# 保存题目数据
def save_questions(questions):
    with open("questions.json", "w", encoding="utf-8") as file:
        json.dump(questions, file, ensure_ascii=False, indent=4)


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




@app.route('/look/<int:question_id>')
def look(question_id):
    try:
        return render_template(f'./题目/{question_id}.html')
    except UnicodeDecodeError:
        return render_template('error.html', error='编码错误')


@app.route('/example/<int:question_id>')
def show_example_code(question_id):
    questions = load_questions()
    question = next((q for q in questions if q['id'] == question_id), None)
    if question:
        example_code = question.get('example_code', '无示例代码')
        save = question.get('save', "False")
        return render_template('example_code.html', question=question, example_code=example_code, to=str(question_id), save=save)
    return redirect(url_for('unfind'))



# 自动判题逻辑

def check_html(html_code, question):
    try:
        soup = BeautifulSoup(html_code, 'html.parser')
    except Exception as e:
        return f"HTML 解析错误: {str(e)}"

    # 移除所有的 <style> 标签
    for style in soup.find_all('style'):
        style.decompose()

    # 检查必需的标签
    # missing_tags = [tag for tag in question['required_tags'] if not soup.find(tag.strip())]
    # if missing_tags:
    #     return f"缺少以下标签: {', '.join(missing_tags)}"

    # 检查未闭合或内容为空的标签
    unclosed_tags = []
    for tag in question['required_tags']:
        tag_elements = soup.find_all(tag.strip())
        for element in tag_elements:
            if not element.find_all(recursive=False) and not element.get_text(strip=True):
                unclosed_tags.append(tag.strip())
    if unclosed_tags:
        return f"以下标签未正确闭合或内容为空: {', '.join(unclosed_tags)}"

    # 检查关键字
    text_content = soup.get_text()
    text_content = text_content.replace('input', ' ')
    missing_keywords = [word.strip() for word in question['keywords'] if word.strip() not in text_content]
    if missing_keywords:
        return f"缺少以下关键字: {', '.join(missing_keywords)}"

    # 检查 <img> 标签的 alt 属性
    for img in soup.find_all('img'):
        if not img.get('alt'):
            return "所有 <img> 标签必须包含 alt 属性"

    # 检查 <a> 标签的 href 属性
    for a in soup.find_all('a'):
        if not a.get('href'):
            return "所有 <a> 标签必须包含 href 属性"

    # 检查 meta 标签
    # if not soup.find('meta', attrs={'charset': True}):
    #     return "缺少字符集 <meta charset='UTF-8'> 标签，如果没有将可能导致页面显示乱码"

    # 检查是否存在 <title> 内容
    try:
        title = soup.find('title').get_text(strip=True)
        if not title:
            return "<title> 标签内容不能为空"
    except Exception:
        pass

    # 检查是否存在多余的空白标签
    empty_tags = ['p', 'div', 'span']
    for tag in empty_tags:
        for element in soup.find_all(tag):
            if not element.get_text(strip=True):
                return f"存在内容为空的 <{tag}> 标签"

    # 检查 <script> 标签
    for script in soup.find_all('script'):
        if not script.get('src'):
            return "所有 <script> 标签必须包含 src 属性"

    # 检查 <link> 标签
    for link in soup.find_all('link'):
        if not link.get('href'):
            return "所有 <link> 标签必须包含 href 属性"
    a = check_html_closing_tags(html_code)
    # 检查闭合标签是否正确
    if '未正确闭合的标签' in a:
        return a
    elif '以下标签未正确闭合' in a:
        return a

    return "代码检查通过！"



# 初始化数据
users = load_users()
user_completed_questions = load_user_completed_questions()


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form['password']
        if password == '070313':
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else:
            return render_template('admin_login.html', error='密码错误')
    return render_template('admin_login.html')


@app.route('/submit_html_check', methods=['POST'])
def submit_html_check():
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))

    html_code = request.form['code']
    question = {
        'required_tags': [],  # 在这里可以定义必需的标签
        'keywords': []  # 在这里可以定义关键词
    }

    result = check_html(html_code, question)

    # 重新渲染 admin.html 并传递检查结果
    questions = load_questions()  # 重新加载问题
    return render_template('admin.html', questions=questions, check_result=result)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username] == password:
            session['username'] = username
            if username not in user_completed_questions:
                user_completed_questions[username] = []
            return redirect(url_for('user_home'))
        else:
            return render_template('login.html', error='用户名或密码错误')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # 检查用户名是否已存在
        if username in users:
            return render_template('register.html', error='用户名已存在')

        # 保存新用户
        users[username] = password
        save_users(users)

        # 初始化用户已完成问题的记录
        user_completed_questions[username] = []  # 确保有一个空列表
        save_user_completed_questions(user_completed_questions)  # 保存到文件

        session['username'] = username
        return redirect(url_for('user_home'))

    return render_template('register.html')

@app.route('/admin/variables')
def show_variables():
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
    questions = load_questions()
    # 提取所有变量
    variables = {
        'USERS_FILE': USERS_FILE,
        'COMPLETED_QUESTIONS_FILE': COMPLETED_QUESTIONS_FILE,
        'users': users,
        'user_completed_questions': user_completed_questions,
        'session': session,
        "questions": questions,

    }

    # 格式化变量为 "变量名=变量值" 的形式
    formatted_variables = "\n".join(f"{name}={value}" for name, value in variables.items())

    return render_template('variables.html', variables=formatted_variables)


@app.route('/admin')
def admin():
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
    questions = load_questions()
    return render_template('admin.html', questions=questions)


@app.route('/unfind')
def unfind():
    return render_template('unfind.html')


@app.route('/admin/add', methods=['POST'])
def add_question():
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
    questions = load_questions()
    interests = request.form.getlist('interests')
    if "save" in str(interests):
        new_question = {
            "id": len(questions) + 1,
            "title": request.form['title'],
            "description": request.form['description'],
            "required_tags": request.form['required_tags'].split(","),
            "keywords": request.form['keywords'].split(","),
            "example_code": request.form['example_code'],
            "save": "True",
        }
        with open("./templates/题目/" + str(len(questions) + 1) + ".html", 'w') as f:
            f.write(request.form['example_code'])

    else:
        new_question = {
            "id": len(questions) + 1,
            "title": request.form['title'],
            "description": request.form['description'],
            "required_tags": request.form['required_tags'].split(","),
            "keywords": request.form['keywords'].split(","),
            "example_code": request.form['example_code'],
            "save": "False",
        }


    questions.append(new_question)
    save_questions(questions)
    return redirect(url_for('admin'))

@app.route('/admin/modify', methods=['GET', 'POST'])
def modify_variables():
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        # 获取所有需要修改的变量，这里以用户和已完成的问题为例
        new_users = request.form.get('users')
        new_completed_questions = request.form.get('completed_questions')

        # 处理新的用户信息
        if new_users:
            try:
                users_data = json.loads(new_users)
                save_users(users_data)
            except json.JSONDecodeError:
                return render_template('modify.html', error='用户数据格式不正确')

        # 处理新的已完成的问题
        if new_completed_questions:
            try:
                completed_data = json.loads(new_completed_questions)
                save_user_completed_questions(completed_data)
            except json.JSONDecodeError:
                return render_template('modify.html', error='完成问题数据格式不正确')

        return redirect(url_for('admin'))

    return render_template('modify.html', users=users, completed_questions=user_completed_questions, questions=load_questions())


@app.route('/admin/delete/<int:id>')
def delete_question(id):
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
    questions = load_questions()
    questions = [q for q in questions if q['id'] != id]
    save_questions(questions)
    try:
        os.remove("./templates/题目/" + str(id) + ".html")
    except FileNotFoundError:
        pass
    return redirect(url_for('admin'))


@app.route('/questions')
def questions():
    questions = load_questions()
    user_questions = user_completed_questions.get(session.get('username'), [])
    return render_template('questions.html', questions=questions, user_completed_questions=user_questions)


@app.route('/admin/nav')
def admin_nav():
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
    return render_template('admin_nav.html')


from datetime import datetime


@app.route('/submit/<int:question_id>', methods=['POST'])
def submit_code(question_id):
    question = next((q for q in load_questions() if q['id'] == question_id), None)
    if question:
        html_code = request.form['code']
        result = check_html(html_code, question)

        # 获取当前时间
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d %H:%M:%S")  # 格式化日期

        # 确定状态
        status = "PASS" if result == "代码检查通过！" else "NO PASS"

        # 保存提交的代码到JSON文件
        submission_entry = {
            "username": session.get('username'),
            "date": date_str,
            "status": status,
            "message": result
        }

        submission_key = f"{submission_entry['username']} {submission_entry['date']} {submission_entry['status']} 检查结果:{submission_entry['message']}"

        # 加载已有的提交记录
        if os.path.exists('submissions.json'):
            with open('submissions.json', 'r', encoding='utf-8') as file:
                submissions = json.load(file)
        else:
            submissions = {}

        submissions[submission_key] = html_code

        # 保存更新后的提交记录
        with open('submissions.json', 'w', encoding='utf-8') as file:
            json.dump(submissions, file, ensure_ascii=False, indent=4)

        # 确保用户的完成记录被初始化
        username = session.get('username')
        if username not in user_completed_questions:
            user_completed_questions[username] = []  # 初始化为空列表

        if status == "PASS":
            user_completed_questions[username].append(question_id)  # 记录通过的题目
            save_user_completed_questions(user_completed_questions)  # 保存到文件

        return render_template('result.html', result=result)

    return redirect(url_for('unfind'))


@app.route('/submit/<int:question_id>')
def submit(question_id):
    question = next((q for q in load_questions() if q['id'] == question_id), None)
    user_questions = user_completed_questions.get(session.get('username'), [])
    if question:
        return render_template('submit.html', question=question, user_completed_questions=user_questions)
    return redirect(url_for('unfind'))


@app.route('/user/home')
def user_home():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    completed_questions = user_completed_questions.get(username, [])
    total_submitted = len(completed_questions)  # 总交题数

    if total_submitted > 0:
        status_message = f"已解决 {total_submitted} 题"
    else:
        status_message = "尚未通过任何题目。"

    return render_template('user_home.html', username=username,
                           total_submitted=total_submitted,
                           completed_questions=completed_questions,
                           status_message=status_message)



@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)  # 同时清除用户名
    return redirect(url_for('home'))

@app.route('/user/submissions')
def user_submissions():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    submissions = {}

    # 读取提交记录
    if os.path.exists('submissions.json'):
        with open('submissions.json', 'r', encoding='utf-8') as file:
            submissions = json.load(file)

    # 过滤出当前用户的提交记录
    user_submissions = {k: v for k, v in submissions.items() if k.startswith(username)}

    return render_template('submissions.html', user_submissions=user_submissions)

@app.errorhandler(405)
def handle_405_error(error):
    return render_template('302_error.html'), 405

if __name__ == '__main__':
    # 初始化用户文件和完成问题文件
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            f.write("{}")  # 初始化空的用户字典
    if not os.path.exists(COMPLETED_QUESTIONS_FILE):
        with open(COMPLETED_QUESTIONS_FILE, "w") as f:
            f.write("{}")  # 初始化空的已完成问题字典

    app.run(host='0.0.0.0', port=5000, debug=True)
