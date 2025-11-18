import discord
from discord.ext import commands
import random
import os
import asyncio
from discord import app_commands

# DeepSeek 个人API（你已充值成功）
from openai import AsyncOpenAI

client = AsyncOpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v1"
)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)
TOKEN = os.getenv('DISCORD_TOKEN')

@bot.event
async def on_ready():
    print(f'{bot.user} 已上线！命运转盘 + 金币预测模式启动~')
    try:
        synced = await bot.tree.sync()
        print(f'同步了 {len(synced)} 个slash命令')
    except Exception as e:
        print(e)

# ============================= /coin 金币预测 =============================
@app_commands.describe(stock="输入你希望被好运祝福的代码")
@app_commands.describe(day="选择预测日期：今天 或 明天")
@app_commands.choices(day=[
    app_commands.Choice(name='今天', value='today'),
    app_commands.Choice(name='明天', value='tomorrow')
])
@bot.tree.command(name='coin', description='用好运硬币预测股票涨跌！')
async def coin(interaction: discord.Interaction, stock: str, day: str):
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

# ============================= /buy 超级命运转盘（DeepSeek实时热度 + 兜底七姐妹 + 日志打印） =============================
@bot.tree.command(name='buy', description='每日自动热度转盘 + 实时原因，直接转！')
async def buy(interaction: discord.Interaction):
    await interaction.response.defer()

    # 1. DeepSeek实时选今日最热7股 + 日志记录
    try:
        prompt = "根据今天（2025年11月19日）全球股市实时热度和新闻，直接列出最热门的7只美股或加密货币代码（大写），只输出7个代码，用逗号分隔，不要任何解释"
        completion = await client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50,
            temperature=0.5
        )
        hot_str = completion.choices[0].message.content.strip()
        hot7 = [code.strip() for code in hot_str.split(',') if code.strip()]
        if len(hot7) < 7:
            raise Exception("DeepSeek返回不足7只")
        print(f"[BUY] 使用 DeepSeek 实时热度7股: {hot7}")
    except Exception as e:
        print(f"[BUY] DeepSeek 抓取失败，回退到七姐妹兜底: {e}")
        hot7 = ['AAPL', 'MSFT', 'GOOG', 'AMZN', 'META', 'NVDA', 'TSLA']

    # 2. 固定8个
    fixed = ['TQQQ', 'SQQQ', 'BTC', 'BABA', 'NIO', 'UVXY', '不操作', '清仓']
    all_options = list(dict.fromkeys(hot7 + fixed))

    winner = random.choice(all_options)

    # 3. 转盘动画
    full_wheel = all_options * random.randint(2, 3)
    k = random.randint(5, min(15, len(full_wheel)))
    fast_sequence = [full_wheel[i] for i in random.sample(range(len(full_wheel)), k)]

    slow_sequence = []
    for _ in range(random.randint(3, 6)):
        slow_sequence.append(random.choice(all_options))
    spin_sequence = fast_sequence + slow_sequence

    embed = discord.Embed(title="**今天买什么？** 🛍️", description="🎰 **大转盘启动中... 转啊转~**", color=0x3498DB)
    await interaction.followup.send(embed=embed)

    for i, current in enumerate(spin_sequence):
        await asyncio.sleep(0.2 if i < len(fast_sequence) else 0.5 + (i - len(fast_sequence))*0.1)
        arrow = " **→** " if i < len(spin_sequence)-1 else " **→** "
        embed.description = f"### 🎰 **转动中... 当前: {current}{arrow}** ###"
        await interaction.edit_original_response(embed=embed)

    await asyncio.sleep(0.8)

    # 4. 生成一句真实原因
    prompt = f"用一句简要真实的原因总结今天买{winner}的理由，严格15-25字以内，无迷信"
    completion = await client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=30,
        temperature=0.8
    )
    reason = completion.choices[0].message.content.strip()
    reason = (reason[:25] + '...') if len(reason) > 25 else reason

    # 5. 最终结果（最大字 + <代码> + 🤑保留）
    if winner in ['不操作', '清仓']:
        final = f"转盘停下！🎉\n### 今天建议 <**{winner}**> ###\n{reason}"
    else:
        final = f"转盘停下！🎉\n### 今天推荐买 <**{winner}**> 🤑 ###\n{reason}"

    embed.description = final
    embed.set_footer(text="")
    await interaction.edit_original_response(embed=embed)

if __name__ == '__main__':
    if not TOKEN:
        raise ValueError('请设置DISCORD_TOKEN环境变量！')
    bot.run(TOKEN)
