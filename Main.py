import discord
from discord.ext import commands
import random
import os

# 设置Bot意图（slash commands需要）
intents = discord.Intents.default()
intents.message_content = True  # 如果需要读取消息

bot = commands.Bot(command_prefix='!', intents=intents)  # !是备用前缀，但我们用slash

# 替换为你的Bot Token
TOKEN = os.getenv('DISCORD_TOKEN')  # 建议用环境变量存储Token

@bot.event
async def on_ready():
    print(f'{bot.user} 已上线！')  # Bot启动时打印
    try:
        synced = await bot.tree.sync()  # 同步slash commands
        print(f'同步了 {len(synced)} 个slash命令')
    except Exception as e:
        print(e)

# Slash命令：/lucky_coin
@bot.tree.command(name='lucky_coin', description='扔一个好运硬币，看看你的运气！')
async def lucky_coin(interaction: discord.Interaction):
    # 随机结果
    result = random.choice(['🪙 正面 - 大吉！今天超级幸运！', '🪙 反面 - 小凶... 别灰心，再试试？'])
    # 发送回复
    await interaction.response.send_message(result, ephemeral=False)  # ephemeral=True 可以私聊回复

# 运行Bot
if __name__ == '__main__':
    if not TOKEN:
        raise ValueError('请设置DISCORD_TOKEN环境变量！')
    bot.run(TOKEN)
