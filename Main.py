import discord
from discord.ext import commands
import random
import os
import asyncio  # 用于sleep动画
from discord import app_commands  # 用于describe和choices参数

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

# 原命令：/lucky stock:字符串（股票代码） day:选择（今天/明天，必选）
@app_commands.describe(stock="输入你希望被好运祝福的代码")
@app_commands.describe(day="选择预测日期：今天 或 明天")
@app_commands.choices(day=[
    app_commands.Choice(name='今天', value='today'),
    app_commands.Choice(name='明天', value='tomorrow')
])
@bot.tree.command(name='lucky', description='用好运硬币预测股票涨跌！输入股票代码和日期试试运气~')
async def lucky(interaction: discord.Interaction, stock: str, day: str):
    # 验证股票代码（简单，大写转换）
    stock = stock.upper().strip()
    if not stock:
        await interaction.response.send_message("哎呀，股票代码不能为空！试试 /lucky stock:TSLA day:今天", ephemeral=True)
        return
    
    # 随机结果：0=正面(涨), 1=反面(跌)
    result = random.choice([0, 1])
    is_up = result == 0  # True=涨
    
    # 日期间翻译（中文显示）
    day_text = '今天' if day == 'today' else '明天'
    
    # 问题文本（加🪙和🙏）
    question = f"🪙硬币啊~硬币~告诉我{day_text}{stock}是涨还是跌？🙏"
    
    # 创建Embed（固定蓝色，无其他文字，只GIF）
    embed = discord.Embed(title=question, color=0x3498DB)  # 固定Discord蓝
    
    # URL 模式：根据结果选择Imgur GIF
    if is_up:
        embed.set_image(url='https://i.imgur.com/hXY5B8Z.gif')  # 涨的GIF
    else:
        embed.set_image(url='https://i.imgur.com/co0MGhu.gif')  # 跌的GIF
    
    await interaction.response.send_message(embed=embed)

# 新命令：/buy codes:字符串（逗号分隔，无需手动添加）
@app_commands.describe(codes="输入股票代码，用逗号分隔，至少2个 e.g. AAPL,TSLA,GOOG (最多10个)")
@bot.tree.command(name='buy', description='幸运大转盘：今天买什么？输入代码列表（逗号分隔），转盘选一个推荐~')
async def buy(interaction: discord.Interaction, codes: str):
    # 先defer，防3s响应限（动画需时）
    await interaction.response.defer()
    
    # 解析代码列表
    codes_list = [c.strip().upper() for c in codes.split(',') if c.strip()]
    if len(codes_list) < 2:
        await interaction.followup.send("哎呀，至少填2个股票代码！试试 /buy codes:AAPL,TSLA", ephemeral=True)
        return
    if len(codes_list) > 10:
        await interaction.followup.send("最多10个代码哦~ 简化列表试试！", ephemeral=True)
        return
    
    # 随机选赢家
    winner = random.choice(codes_list)
    
    # 构建轮盘序列：快转几圈 + 慢停到赢家
    full_wheel = codes_list * random.randint(2, 3)  # 2-3圈
    # 修复：k <= len(full_wheel)，最小1步（小列表时），目标5-15
    k = random.randint(1, len(full_wheel))
    if len(full_wheel) >= 5:
        k = random.randint(5, min(15, len(full_wheel)))
    fast_spins = random.sample(range(len(full_wheel)), k)  # 安全采样
    fast_sequence = [full_wheel[i] for i in fast_spins]
    
    # 慢停序列：从随机点渐近赢家
    slow_start = random.choice(codes_list)
    slow_sequence = [slow_start]
    slow_steps = random.randint(1, min(6, len(codes_list)))  # 动态慢步，防小列表
    for _ in range(slow_steps):  # 1-6步慢转
        next_code = random.choice(codes_list)
        slow_sequence.append(next_code)
    slow_sequence.append(winner)  # 最终停
    
    # 总序列
    spin_sequence = fast_sequence + slow_sequence
    
    # 初始Embed（标题大字）
    embed = discord.Embed(title="🎰 **今天买什么？** 🛍️", description="🌀 **大转盘启动中... 转啊转~**", color=0x3498DB)
    embed.set_footer(text="纯娱乐推荐，投资需谨慎哦~")
    await interaction.followup.send(embed=embed)
    
    # 动画：编辑Embed显示当前“指针”（用**bold**让代码字大）
    for i, current in enumerate(spin_sequence):
        # 延迟：快转0.2s，慢转渐增0.5-1s
        if i < len(fast_sequence):
            await asyncio.sleep(0.2)
        else:
            await asyncio.sleep(0.5 + (i - len(fast_sequence)) * 0.1)  # 慢到1s
        
        # 更新描述：显示当前代码 + 箭头效果（**bold**字大）
        arrow = " **→** " if i < len(spin_sequence) - 1 else " **✅**"
        embed.description = f"🌀 **转动中... 当前: {current}{arrow}**"
        await interaction.edit_original_response(embed=embed)
    
    # 最终停：推荐赢家（大字bold）
    embed.description = f"🎉 **转盘停下！** 今天推荐买: **{winner}** 🤑"
    await interaction.edit_original_response(embed=embed)

# 运行Bot
if __name__ == '__main__':
    if not TOKEN:
        raise ValueError('请设置DISCORD_TOKEN环境变量！')
    bot.run(TOKEN)
