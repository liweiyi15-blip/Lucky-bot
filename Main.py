import discord
from discord.ext import commands
import random
import os
from discord import app_commands  # 用于describe参数

# 设置Bot意图
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# 替换为你的Bot Token（用环境变量）
TOKEN = os.getenv('DISCORD_TOKEN')

@bot.event
async def on_ready():
    print(f'{bot.user} 已上线！好运硬币股票预测模式启动~')
    try:
        synced = await bot.tree.sync()
        print(f'同步了 {len(synced)} 个slash命令')
    except Exception as e:
        print(e)

# Slash命令：/lucky stock:字符串（股票代码）
@app_commands.describe(stock="输入你希望被好运祝福的代码")
@bot.tree.command(name='lucky', description='用好运硬币预测明天股票涨跌！输入股票代码试试运气~')
async def lucky(interaction: discord.Interaction, stock: str):
    # 验证股票代码（简单，大写转换）
    stock = stock.upper().strip()
    if not stock:
        await interaction.response.send_message("哎呀，股票代码不能为空！试试 /lucky stock:TSLA", ephemeral=True)
        return
    
    # 随机结果：0=正面(涨), 1=反面(跌)
    result = random.choice([0, 1])
    is_up = result == 0  # True=涨
    
    # 问题文本（加🪙和🙏）
    question = f"🪙硬币啊~硬币~告诉我明天{stock}是涨还是跌？🙏"
    
    # 创建Embed（标题为问题，无其他文字，只GIF）
    embed = discord.Embed(title=question, color=0x00ff00 if is_up else 0xff0000)
    
    # URL 模式：根据结果选择Imgur GIF
    if is_up:
        embed.set_image(url='https://i.imgur.com/hXY5B8Z.gif')  # 涨的GIF
    else:
        embed.set_image(url='https://i.imgur.com/co0MGhu.gif')  # 跌的GIF
    
    await interaction.response.send_message(embed=embed)

# 运行Bot
if __name__ == '__main__':
    if not TOKEN:
        raise ValueError('请设置DISCORD_TOKEN环境变量！')
    bot.run(TOKEN)
