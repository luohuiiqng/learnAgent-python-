import torch
import matplotlib.pyplot as plt

# 三组样本满足 y = 2x。模型只有一个权重 w，训练的目标是让 w 学到 2。
x_data = [1.0,2.0,3.0]
y_data = [2.0,4.0,6.0]

# w 必须是 Tensor。后面的乘法和减法才会被 PyTorch 记录成计算图，才能自动求梯度。
# 初值是 1.0。训练前 forward(4) = 4，而 4 * 2 = 8，所以一开始预测偏小。
w = torch.Tensor([1.0])
# 只有 requires_grad=True 的张量，反向传播时才会把 ∂loss/∂w 累加进 w.grad。
w.requires_grad = True


def forward(x):
    # 前向计算：y_pred = x * w。
    # x 是 Python 浮点数，w 是 Tensor，结果也是 Tensor，并且挂在以 w 为叶子的计算图上。
    return x*w

def loss(x,y):
    y_pred = forward(x)
    # 平方误差。对 w 的导数是 2 * (y_pred - y) * x。
    # y_pred < y 时导数为负，后面用“减去学习率乘梯度”会把 w 往上推。
    return (y_pred - y)**2


# .item() 从只有一个元素的 Tensor 里取出 Python 浮点数，方便打印。
# 这里还没训练，w 仍是 1，所以预测值是 4.0。
print("predict (before traing)",4,forward(4).item())


#训练
# epoch_losses：每一轮三个样本损失的平均值，用来画损失曲线。
# grads：每一次更新参数之前的 w.grad，用来画梯度曲线。
epoch_losses = []
grads = []
for epoch in range(100):
    loss_sum = 0.0
    # 一个样本算一次损失、更新一次权重，这是随机梯度下降。
    for x,y in zip(x_data,y_data):
        # 前向：用当前的 w 算出这个样本的损失，同时建好这一步的计算图。
        l = loss(x,y)
        # 反向：从标量 l 往回求导，把 ∂l/∂w 累加到 w.grad。
        l.backward()
        # .item() 只用于记录和打印，不参与参数更新。
        grad = w.grad.item()
        grads.append(grad)
        print('\tgrad:',x,y,grad)
        # 用 .data 改数值，这次减法不会进入计算图，w 仍然是叶子张量。
        # 学习率 0.01。梯度为负时，w 增大，朝真实值 2 靠近。
        w.data = w.data - 0.01*w.grad.data

        # PyTorch 默认把梯度累加到 w.grad 上。
        # 这次更新已经用完梯度，必须清零，下一个样本的 backward 才不会叠加上旧梯度。
        w.grad.data.zero_()
        # l 是更新前的损失。三个样本各自用的 w 不同，因为每步都改了权重。
        loss_sum += l.item()

    mean_loss = loss_sum / len(x_data)
    epoch_losses.append(mean_loss)
    # 控制台打印的是本轮最后一个样本的损失，数值和上面的平均损失不一样。
    print("process:",epoch,l.item())

# 训练结束后 w 接近 2，forward(4) 接近 8。
print("predict (after traing)",4,forward(4).item())

# Microsoft YaHei 用来显示中文标题。
# axes.unicode_minus 让坐标轴上的负号用普通减号，避免在对数刻度里显示成方块。
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

plt.figure(figsize=(10, 4))

plt.subplot(1, 2, 1)
plt.plot(epoch_losses)
# 损失从约 1 降到约 1e-12。线性坐标会把后面的下降压成贴着横轴的线，所以用对数坐标。
plt.yscale("log")
plt.xlabel("epoch")
plt.ylabel("loss")
plt.title("每个 epoch 的平均损失")
plt.grid(True)

plt.subplot(1, 2, 2)
plt.plot(grads)
# 每轮有 3 步，x 依次是 1、2、3。x 越大梯度绝对值越大，所以曲线呈锯齿，并整体趋近 0。
plt.xlabel("step")
plt.ylabel("grad")
plt.title("每一步的梯度")
plt.grid(True)

plt.tight_layout()
# 图片保存在脚本所在目录。plt.show() 会停住，关掉窗口后程序才结束。
plt.savefig("损失和梯度.png", dpi=120)
plt.show()
