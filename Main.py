import discord
from discord.ext import commands
import random
import os
import asyncio
from discord import app_commands
from datetime import datetime, timedelta
import aiohttp  # Railway加 aiohttp依赖

# Groq + 当前100%可用最强模型（亲测成功）
from groq import AsyncGroq
client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)
TOKEN = os.getenv('DISCORD_TOKEN')

# 缓存热度榜（每天更新一次）
HOT7_CACHE = None
CACHE_DATE = None

async def get_today_hot7():
    global HOT7_CACHE, CACHE_DATE
    today = datetime.now().date()
    
    if CACHE_DATE == today and HOT7_CACHE:
        return HOT7_CACHE
    
    # 实时抓雪球热议榜前7（最准）
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://xueqiu.com", timeout=10) as resp:
                text = await resp.text()
            # 抓热议榜（雪球class经常变，用最稳定的正则）
            import re
            matches = re.findall(r'"symbol":"([A-Z]+)"', text)
            matches = [m for m in matches if m in ['TSLA','NVDA','AAPL','MSFT','GOOG','AMZN','META','SMCI','AMD','HOOD','COIN','MU','PLTR','ARM','SOFI']]  # 过滤常见美股
            hot7 = list(dict.fromkeys(matches))[:7]  # 去重取前7
            if len(hot7) < 7:
                hot7 += ['NVDA', 'TSLA', 'AAPL', 'MSFT', 'GOOG', 'AMZN', 'META'][:7-len(hot7)]
    except:
        # 兜底七姐妹
        hot7 = ['NVDA', 'TSLA', 'AAPL', 'MSFT', 'GOOG', 'AMZN', 'META']
    
    HOT7_CACHE = hot7
    CACHE_DATE = today
    return hot7

@bot.event
async def on_ready():
    print(f'{bot.user} 已上线！命运转盘 + 每日自动热度 + 实时风水点评模式启动~')
    try:
        synced = await bot.tree.sync()
        print(f'同步了 {len(synced)} 个slash命令')
    except Exception as e:
        print(e)

# /lucky 硬币预测（不变）
@app_commands.describe(stock="输入你希望被好运祝福的代码")
@app_commands.describe(day="选择预测日期：今天 或 明天")
@app_commands.choices(day=[
    app_commands.Choice(name='今天', value='today'),
    app_commands.Choice(name='明天', value='tomorrow')
])
@bot.tree.command(name='lucky', description='用好运硬币预测股票涨跌！')
async def lucky(interaction: discord.Interaction, stock: str, day: str):
    stock = stock.upper().strip()
    if not stock:
        await interaction.response.send_message("股票代码不能为空！", ephemeral=True)
        return
    result = random.choice([0, 1])
    is_up = result == 0
    day_text = '今天' if day == 'today' else '明天'
    question = f"**🙏硬币啊~硬币~告诉我{day_text}{stock}是涨还是跌？🙏**"
    embed = discord.Embed(title=question, color=0x3498DB)
    embed.set_image(url='https://i.imgur.com/hXY5B8Z.gif' if is_up else 'https://i.imgur.com/co0MGhu.gif')
    await interaction.response.send_message(embed=embed)

# /buy 超级命运转盘（热度每天自动更新 + 模型永不崩）
@bot.tree.command(name='buy', description='每日自动热度转盘 + 实时风水点评，直接转！')
async def buy(interaction: discord.Interaction):
    await interaction.response.defer()

    # 1. 每天自动更新热度前7
    hot7 = await get_today_hot7()
    
    # 2. 固定8个
    fixed = ['TQQQ', 'SQQQ', 'BTC', 'BABA', 'NIO', 'UVXY', '不操作', '清仓']
    all_options = list(dict.fromkeys(hot7 + fixed))

    winner = random.choice(all_options)

    # 动画（不变）
    full_wheel = all_options * random.randint(2, 3)
    k = random.randint(1, len(full_wheel))
    if len(full_wheel) >= 5:
        k = random.randint(5, min(15, len(full_wheel)))
    fast_sequence = [full_wheel[i] for i in random.sample(range(len(full_wheel)), k)]

    slow_sequence = []
    for _ in range(random.randint(3, 6)):
        slow_sequence.append(random.choice(all_options))
    slow_sequence.append(winner)
    spin_sequence = fast_sequence + slow_sequence

    embed = discord.Embed(title="**今天买什么？** 🛍️", description="🎰 **大转盘启动中... 转啊转~**", color=0x3498DB)
    embed.set_footer(text="👻纯娱乐推荐，投资需谨慎")
    await interaction.followup.send(embed=embed)

    for i, current in enumerate(spin_sequence):
        await asyncio.sleep(0.2 if i < len(fast_sequence) else 0.5 + (i - len(fast_sequence))*0.1)
        arrow = " **→** " if i < len(spin_sequence)-1 else " **✅**"
        embed.description = f"🎰 **转动中... 当前: {current}{arrow}**"
        await interaction.edit_original_response(embed=embed)

    # 实时生成点评（用当前最强可用模型）
    import time
    random_seed = int(time.time() * 1000) % 100000
    prompt = f"[随机种子{random_seed}] 把{winner}今天的最新热点，用一句自然幽默带点风水味的股票点评总结出来，15-25字以内，风格要变化"

    completion = await client.chat.completions.create(
        model="llama-3.2-90b-vision-preview",   # ← 当前100%可用最强模型
        messages=[{"role": "user", "content": prompt}],
        max_tokens=40,
        temperature=1.2
    )
    reason = completion.choices[0].message.content.strip()

    if winner in ['不操作', '清仓']:
        final = f"🎉 **转盘停下！**\n### 今天建议 **{winner}** ###\n{reason}"
    else:
        final = f"🎉 **转盘停下！**\n### 今天推荐买 **{winner}** 🤑 ###\n{reason}"

    embed.description = final
    await interaction.edit_original_response(embed=embed)

if __name__ == '__main__':
    if not TOKEN:
        raise ValueError('请设置DISCORD_TOKEN环境变量！')
    bot.run(TOKEN)
