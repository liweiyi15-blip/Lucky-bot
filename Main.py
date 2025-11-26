import discord
from discord.ext import commands
import random
import os
import asyncio
from discord import app_commands
from openai import AsyncOpenAI

# =================配置区域=================
client = AsyncOpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v1"
)

# 全局概率配置 (默认值)
trend_config = {
    "mild": 60,   # 60% 概率
    "huge": 35,   # 35% 概率
    "drop": 5     # 5% 概率
}

# ================= GIF 配置区域 =================
# 已替换为你最新提供的25个链接
BUY_GIF_LIST = [
    "https://i.imgur.com/1JK7LqT.gif",
    "https://i.imgur.com/4RZnQvD.gif",
    "https://i.imgur.com/6Ll2d2E.gif",
    "https://i.imgur.com/49LNAPf.gif",
    "https://i.imgur.com/A4xNn8d.gif",
    "https://i.imgur.com/BAamjTj.gif",
    "https://i.imgur.com/Da3176z.gif",
    "https://i.imgur.com/HyX4Psd.gif",
    "https://i.imgur.com/LZnGjF5.gif",
    "https://i.imgur.com/NHK1w7T.gif",
    "https://i.imgur.com/Nx0L7Dp.gif",
    "https://i.imgur.com/OplCEyP.gif",
    "https://i.imgur.com/OpzCvpf.gif",
    "https://i.imgur.com/QUOP8At.gif",
    "https://i.imgur.com/X7uguhk.gif",
    "https://i.imgur.com/XC9LMhr.gif",
    "https://i.imgur.com/fZAHQM5.gif",
    "https://i.imgur.com/kLzEc0L.gif",
    "https://i.imgur.com/joVoooV.gif",
    "https://i.imgur.com/lfodyai.gif",
    "https://i.imgur.com/lsQB4IE.gif",
    "https://i.imgur.com/rO0gQbq.gif",
    "https://i.imgur.com/reopl9v.gif",
    "https://i.imgur.com/vkP96CZ.gif",
    "https://i.imgur.com/weOKobo.gif"
]

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
TOKEN = os.getenv('DISCORD_TOKEN')

@bot.event
async def on_ready():
    print(f'{bot.user} 已上线！')
    print(f'当前概率配置: 温和涨={trend_config["mild"]}%, 暴涨={trend_config["huge"]}%, 下跌={trend_config["drop"]}%')
    try:
        synced = await bot.tree.sync()
        print(f'同步了 {len(synced)} 个slash命令')
    except Exception as e:
        print(e)

# ================= 1. /coin 金币预测 =================
@app_commands.describe(stock="输入你希望被好运祝福的代码")
@app_commands.describe(day="选择预测日期：今天 或 明天")
@app_commands.choices(day=[
    app_commands.Choice(name='今天', value='today'),
    app_commands.Choice(name='明天', value='tomorrow')
])
@bot.tree.command(name='coin', description='用好运硬币预测股票涨跌！')
async def coin(interaction: discord.Interaction, stock: str, day: str):
    stock = stock.upper().strip()
    result = random.choice([0, 1])
    is_up = result == 0
    day_text = '今天' if day == 'today' else '明天'
    
    question = f"**🙏硬币啊~硬币~告诉我{day_text}{stock}是涨还是跌？🙏**"
    embed = discord.Embed(title=question, color=0x3498DB)
    embed.set_image(url='https://i.imgur.com/hXY5B8Z.gif' if is_up else 'https://i.imgur.com/co0MGhu.gif')
    await interaction.response.send_message(embed=embed)

# ================= 2. /buy 命运转盘 (纯净版) =================
@bot.tree.command(name='buy', description='转盘会告诉你买什么。。。')
async def buy(interaction: discord.Interaction):
    # 随机选择一个GIF
    if BUY_GIF_LIST:
        gif_url = random.choice(BUY_GIF_LIST)
    else:
        # 防止列表为空的备用图
        gif_url = "https://i.imgur.com/1JK7LqT.gif"

    # 构建 Embed
    embed = discord.Embed(
        title="决定命运的转盘~转起来吧~🎰🎰",
        color=0xE74C3C 
    )
    embed.set_image(url=gif_url)
    embed.set_footer(text="纯娱乐推荐，投资需谨慎👻")
    
    # 直接发送
    await interaction.response.send_message(embed=embed)

# ================= 3. /trend 走势剧本 (占卜预测版) =================
@app_commands.describe(stock="输入你想看剧本的代码（如 TSLA）")
@bot.tree.command(name='trend', description='占卜预测今日股票走势')
async def trend(interaction: discord.Interaction, stock: str):
    await interaction.response.defer()
    stock = stock.upper().strip()

    # --- 1. 发送占卜动画 ---
    embed_loading = discord.Embed(
        title=f"🔮 正在为 {stock} 占卜中...",
        description="✨ *观星象，测运势，连接宇宙能量...*",
        color=0x9B59B6
    )
    message = await interaction.followup.send(embed=embed_loading)

    # --- 2. 后台计算 ---
    p_mild = trend_config['mild']
    p_huge = trend_config['huge']
    
    roll = random.uniform(0, 100)
    
    if roll < p_mild:
        final_percent = random.uniform(0, 10)
    elif roll < (p_mild + p_huge):
        final_percent = random.uniform(10, 15)
    else:
        final_percent = random.uniform(-8, 0)

    sign = "+" if final_percent >= 0 else ""
    percent_str = f"{sign}{final_percent:.1f}%"

    prompt = (
        f"请为股票 {stock} 编造一个今天的走势剧本，风格要像股市解说，带点情绪。"
        f"【硬性要求】：最终收盘必须是 {percent_str}。"
        f"全文字数严格控制在50字以内，越简练越好。"
        f"不要提到具体的百分比数字，只描述过程（开盘、盘中、收盘）。"
    )

    story = ""
    try:
        completion = await client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=80,
            temperature=1.1
        )
        story = completion.choices[0].message.content.strip()
    except Exception as e:
        story = "AI 信号受到宇宙射线干扰..."

    # --- 3. 等待3秒 ---
    await asyncio.sleep(3)

    # --- 4. 结果变身 ---
    color = 0x2ECC71 if final_percent >= 0 else 0xE74C3C 
    emoji = "🚀" if final_percent >= 10 else ("📈" if final_percent >= 0 else "📉")

    embed_final = discord.Embed(title=f"{emoji} {stock} 今日预测", color=color)
    
    embed_final.description = (
        f"### 走势推演 📝\n"
        f"{story}\n\n"
        f"# 最终收盘 {percent_str}"
    )
    embed_final.set_footer(text="*本结果纯属AI胡编，切勿当真*")
    
    await message.edit(embed=embed_final)

# ================= 4. /set_trend 设置概率 (隐藏命令) =================
@app_commands.default_permissions(administrator=True)
@app_commands.describe(mild="温和上涨概率(0-10%区间)", huge="暴涨概率(10-15%区间)", drop="下跌概率(-8-0%区间)")
@bot.tree.command(name='set_trend', description='【管理】设置概率分布')
async def set_trend(interaction: discord.Interaction, mild: int, huge: int, drop: int):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("🚫 你没有权限！", ephemeral=True)
        return

    if mild + huge + drop != 100:
        await interaction.response.send_message(f"🚫 总和必须100！当前: {mild+huge+drop}", ephemeral=True)
        return

    trend_config['mild'] = mild
    trend_config['huge'] = huge
    trend_config['drop'] = drop

    await interaction.response.send_message(
        f"✅ **配置已更新** (此消息仅管理员可见)",
        ephemeral=True
    )

if __name__ == '__main__':
    if not TOKEN:
        print('请设置DISCORD_TOKEN环境变量！')
    else:
        bot.run(TOKEN)
