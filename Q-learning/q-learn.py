import random
from collections import defaultdict
import math

# ------- 简易 4x4 GridWorld 环境 -------
# S: 起点(0), G: 终点(15), X: 坑(5,7,11,12)；到达 G 奖励+1，掉坑-1，其他步-0.01（鼓励更短路径）
class GridWorld:
    def __init__(self, n=4):
        self.n = n
        self.start = 0
        self.goal = n * n - 1
        self.holes = {5, 7, 11, 12}
        self.reset()

    # 1维数据转换为坐标
    def _to_xy(self, s):
        return divmod(s, self.n)
    # 坐标转换为1维数据
    def _to_s(self, x, y):
        return x * self.n + y

    def reset(self):
        self.s = self.start
        return self.s

    # action: 0上 1右 2下 3左
    def step(self, a):
        x, y = self._to_xy(self.s)
        if a == 0 and x > 0: x -= 1
        elif a == 1 and y < self.n - 1: y += 1
        elif a == 2 and x < self.n - 1: x += 1
        elif a == 3 and y > 0: y -= 1
        ns = self._to_s(x, y)

        reward = -0.01
        done = False
        if ns in self.holes:
            reward = -1.0
            done = True
        elif ns == self.goal:
            reward = +1.0
            done = True

        self.s = ns
        return ns, reward, done, {}

    def render(self, path=None):
        path = set(path or [])
        out = []
        for i in range(self.n):
            row = []
            for j in range(self.n):
                s = self._to_s(i, j)
                if s == self.s: cell = "A"     # agent
                elif s == self.start: cell = "S"
                elif s == self.goal: cell = "G"
                elif s in self.holes: cell = "X"
                elif s in path: cell = "."
                else: cell = " "
                row.append(cell)
            out.append("|".join(row))
        print("\n".join(out))
        print()

# ------- Q-learning -------
def q_learning(
    env,
    episodes=2000,
    alpha=0.1,         # 学习率
    gamma=0.99,        # 折扣因子
    eps_start=1.0,     # 起始探索率
    eps_end=0.05,      # 最低探索率
    eps_decay=800,     # 衰减快慢（越小衰减越快）
    max_steps=200
):
    Q = defaultdict(lambda: [0.0, 0.0, 0.0, 0.0])
    returns = []

    def epsilon(t):
        # 指数衰减到 eps_end
        return eps_end + (eps_start - eps_end) * math.exp(-t / eps_decay)

    t = 0
    for ep in range(episodes):
        s = env.reset()
        total_r = 0.0
        for _ in range(max_steps):
            t += 1
            eps = epsilon(t)
            if random.random() < eps:
                a = random.randint(0, 3)
            else:
                qs = Q[s]
                a = max(range(4), key=lambda k: qs[k])

            ns, r, done, _ = env.step(a) #ns:当前位置（一维） r:当前奖励
            total_r += r # 奖励总合

            # 目标：r + gamma * max_a' Q(ns, a')
            best_next = max(Q[ns]) #当前位置 最优奖励
            td_target = r + gamma * best_next
            td_error = td_target - Q[s][a]
            Q[s][a] += alpha * td_error #更新s位置 a动作的 收益

            s = ns
            if done:
                break
        returns.append(total_r)
    return Q, returns

def greedy_policy(Q, s):
    qs = Q[s]
    return max(range(4), key=lambda k: qs[k])

def eval_and_show(env, Q):
    s = env.reset()
    path = [s]
    total_r = 0.0
    for _ in range(50):
        a = greedy_policy(Q, s)
        ns, r, done, _ = env.step(a)
        total_r += r
        path.append(ns)
        s = ns
        if done: break
    print("贪心策略一次评估：累计回报 =", round(total_r, 3))
    env.render(path=path)

if __name__ == "__main__":
    env = GridWorld(n=10)
    Q, rets = q_learning(env)
    # 简单打印学习曲线的最后十个回报
    n = 1000
    print(f"最近{n}回合回报：", [round(x, 2) for x in rets[-n:]])
    eval_and_show(env, Q)
