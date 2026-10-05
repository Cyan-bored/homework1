"""演示用示例代码：一个故意存在问题的用户管理模块。

可以请求 CodeAgent:
- "审查 user_service.py 的代码质量"
- "为 register 函数生成单元测试并运行"
- "解释这个模块的逻辑"
"""


class UserService:
    def __init__(self):
        self.users = {}

    def register(self, username, password):
        if username in self.users:
            return False
        if len(password) < 6:
            return False
        self.users[username] = password
        return True

    def login(self, username, password):
        if self.users.get(username) == password:
            return True
        return False

    def delete(self, username):
        del self.users[username]

    def get_count(self):
        if len(self.users) > 0 == True:
            return len(self.users)
        else:
            return 0
