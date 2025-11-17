import discord
from discord.ext import commands
import random
import os

# 设置Bot意图
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# 替换为你的Bot Token（用环境变量）
TOKEN = os.getenv('DISCORD_TOKEN')

@bot.event
async def on_ready():
    print(f'{bot.user} 已上线！股票硬币预测模式启动~')
    try:
        synced = await bot.tree.sync()
        print(f'同步了 {len(synced)} 个slash命令')
    except Exception as e:
        print(e)

# Slash命令：/predict stock:字符串（股票代码）
@bot.tree.command(name='predict', description='用好运硬币预测明天股票涨跌！输入股票代码试试运气~')
async def predict(interaction: discord.Interaction, stock: str):
    # 验证股票代码（简单，大写转换）
    stock = stock.upper().strip()
    if not stock:
        await interaction.response.send_message("哎呀，股票代码不能为空！试试 /predict stock:AAPL", ephemeral=True)
        return
    
    # 随机结果：0=正面(涨), 1=反面(跌)
    result = random.choice([0, 1])
    is_up = result == 0  # True=涨
    
    # 消息文本
    question = f"硬币啊~硬币~告诉我明天{stock}是涨还是跌？"
    outcome = "🪙 正面 - 明天{stock}要涨啦！大吉！" if is_up else "🪙 反面 - 明天{stock}要跌... 小凶，稳住！"
    disclaimer = "⚠️ 这只是娱乐预测，不是投资建议哦~ 实际以市场为准！"
    
    # 创建Embed，带GIF动画
    embed = discord.Embed(title=question, description=outcome, color=0x00ff00 if is_up else 0xff0000)
    embed.add_field(name="运势", value=disclaimer, inline=False)
    
    # 根据结果选择GIF文件（本地文件）
    gif_path = 'coin_heads.gif' if is_up else 'coin_tails.gif'
    if os.path.exists(gif_path):
        file = discord.File(gif_path)
        embed.set_image(url=f"attachment://{gif_path}")
        await interaction.response.send_message(embed=embed, file=file)
    else:
        # 如果本地文件不存在，用文本+Emoji备用
        embed.set_image(url="https://via.placeholder.com/300x300/FFD700/000000?text=🪙")  # 临时占位
        await interaction.response.send_message(embed=embed)
        print(f"警告：{gif_path} 不存在！请检查文件路径。")

# 运行Bot
if __name__ == '__main__':
    if not TOKEN:
        raise ValueError('请设置DISCORD_TOKEN环境变量！')
    bot.run(TOKEN)
