import discord
from discord.ext import commands
import random
import os
import asyncio
from discord import app_commands
from datetime import datetime

# Groq + 最强永久免费模型
from groq import AsyncGroq
client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)
TOKEN = os.getenv('DISCORD_TOKEN')

@bot.event
async def on_ready():
    print(f'{bot.user} 已上线！命运转盘 + 实时风水点评模式启动~')
    try:
        synced = await bot.tree.sync()
        print(f'同步了 {len(synced)} 个slash命令')
    except Exception as e:
        print(e)

# /lucky 硬币预测（中等GIF + 另起一行 + 大字标题）
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

# /buy 超级命运转盘（最大字结算 + 去热度榜 + 每次点评不一样）
@bot.tree.command(name='buy', description='每日自动热度转盘 + 实时风水点评，直接转！')
async def buy(interaction: discord.Interaction):
    await interaction.response.defer()

    hot7 = ['TSLA', 'NVDA', 'GOOG', 'XPEV', 'CRCL', 'BABA', 'MU']
    fixed = ['TQQQ', 'SQQQ', 'BTC', 'BABA', 'NIO', 'UVXY', '不操作', '清仓']
    all_options = list(dict.fromkeys(hot7 + fixed))

    winner = random.choice(all_options)

    # 动画
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

    # 实时生成点评（最强模型 + 每次都不一样）
    import time
    random_seed = int(time.time() * 1000) % 100000
    prompt = f"[随机种子{random_seed}] 把{winner}今天的最新热点，用一句自然幽默带点风水味的股票点评总结出来，15-25字以内，风格要变化"

    completion = await client.chat.completions.create(
        model="llama3-70b-8192",   # ← 永久免费最强模型
        messages=[{"role": "user", "content": prompt}],
        max_tokens=40,
        temperature=1.2
    )
    reason = completion.choices[0].message.content.strip()

    # 最大号字结算
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
