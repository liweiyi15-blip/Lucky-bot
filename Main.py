import discord
from discord.ext import commands
import random
import os
import asyncio
from discord import app_commands
from openai import AsyncOpenAI

# =================配置区域=================
# DeepSeek 客户端
client = AsyncOpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v1"
)

# 全局概率配置 (默认值)
# mild: 0% ~ 10%
# huge: 10% ~ 15%
# drop: -8% ~ 0%
trend_config = {
    "mild": 60,   # 60% 概率
    "huge": 35,   # 35% 概率
    "drop": 5     # 5% 概率
}

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

# ================= 2. /buy 命运转盘 =================
@bot.tree.command(name='buy', description='每日自动热度转盘 + 实时原因，直接转！')
async def buy(interaction: discord.Interaction):
    await interaction.response.defer()
    
    # 1. 获取代码 (DeepSeek 或 兜底)
    try:
        prompt = "根据今天全球股市实时热度和新闻，列出最热门的7只美股或加密货币代码（大写），用逗号分隔，不要解释"
        completion = await client.chat.completions.create(
            model="deepseek-chat", messages=[{"role": "user", "content": prompt}], max_tokens=50, temperature=0.5
        )
        hot_str = completion.choices[0].message.content.strip()
        hot7 = [code.strip() for code in hot_str.split(',') if code.strip()]
        if len(hot7) < 7: raise Exception("不足7只")
    except:
        hot7 = ['AAPL', 'MSFT', 'GOOG', 'AMZN', 'META', 'NVDA', 'TSLA']

    fixed = ['TQQQ', 'SQQQ', 'BTC', 'BABA', 'NIO', 'UVXY', '不操作', '清仓']
    all_options = list(dict.fromkeys(hot7 + fixed))
    winner = random.choice(all_options)

    # 2. 动画
    embed = discord.Embed(title="**今天买什么？** 🛍️", description="🎰 **大转盘启动中...**", color=0x3498DB)
    await interaction.followup.send(embed=embed)
    
    # 简化的动画逻辑
    await asyncio.sleep(2) 

    # 3. 理由
    prompt_reason = f"用一句简要真实的原因总结今天买{winner}的理由，严格20字以内，无迷信"
    try:
        comp = await client.chat.completions.create(
            model="deepseek-chat", messages=[{"role": "user", "content": prompt_reason}], max_tokens=40
        )
        reason = comp.choices[0].message.content.strip()
    except:
        reason = "AI 暂时掉线，但直觉告诉你买它！"

    final_text = f"转盘停下！🎉\n### 今天推荐 <**{winner}**> ###\n{reason}"
    embed.description = final_text
    await interaction.edit_original_response(embed=embed)

# ================= 3. /trend 走势剧本 (带占卜动画) =================
@app_commands.describe(stock="输入你想看剧本的代码（如 TSLA）")
@bot.tree.command(name='trend', description='AI编造详细走势剧本（新区间+1位小数）')
async def trend(interaction: discord.Interaction, stock: str):
    # 这里先defer，防止超时
    await interaction.response.defer()
    stock = stock.upper().strip()

    # --- 1. 发送占卜动画 (紫色) ---
    embed_loading = discord.Embed(
        title=f"🔮 正在为 {stock} 占卜中...",
        description="✨ *观星象，测运势，连接宇宙能量...*",
        color=0x9B59B6 # 神秘紫
    )
    # 发送第一条消息，并记录下来，稍后编辑它
    message = await interaction.followup.send(embed=embed_loading)

    # --- 2. 后台计算 (同时进行，节省体感时间) ---
    # 读取概率
    p_mild = trend_config['mild']
    p_huge = trend_config['huge']
    
    roll = random.uniform(0, 100)
    
    # 概率逻辑
    if roll < p_mild:
        # 温和涨: 0% ~ 10%
        final_percent = random.uniform(0, 10)
    elif roll < (p_mild + p_huge):
        # 暴涨: 10% ~ 15%
        final_percent = random.uniform(10, 15)
    else:
        # 下跌: -8% ~ 0%
        final_percent = random.uniform(-8, 0)

    # 格式化: 保留1位小数
    sign = "+" if final_percent >= 0 else ""
    percent_str = f"{sign}{final_percent:.1f}%"

    # DeepSeek 编剧本
    prompt = (
        f"请为股票 {stock} 编造一个今天的走势剧本，风格要像股市解说，带点情绪。"
        f"【硬性要求】：最终收盘必须是 {percent_str}。"
        f"全文字数严格控制在60字以内。"
        f"不要提到具体的百分比数字，只描述过程（开盘、盘中、收盘）。"
    )

    story = ""
    try:
        completion = await client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=1.1
        )
        story = completion.choices[0].message.content.strip()
    except Exception as e:
        story = "AI 信号受到宇宙射线干扰..."

    # --- 3. 强制等待 (确保占卜动画展示至少3秒) ---
    await asyncio.sleep(3)

    # --- 4. 最终结果展示 ---
    color = 0x2ECC71 if final_percent >= 0 else 0xE74C3C 
    emoji = "🚀" if final_percent >= 10 else ("📈" if final_percent >= 0 else "📉")

    embed_final = discord.Embed(title=f"{emoji} {stock} 今日预测", color=color)
    
    # 格式：小标题 + 故事 + 空行 + 超大号收盘价
    embed_final.description = (
        f"### 走势推演 📝\n"
        f"{story}\n\n"
        f"# 最终收盘 {percent_str}"
    )
    embed_final.set_footer(text="*本结果纯属AI胡编，切勿当真*")
    
    # 编辑刚才那条“占卜中”的消息
    await message.edit(embed=embed_final)

# ================= 4. /set_trend 设置概率 (管理员用) =================
@app_commands.describe(mild="温和上涨概率(0-10%区间)", huge="暴涨概率(10-15%区间)", drop="下跌概率(-8-0%区间)")
@bot.tree.command(name='set_trend', description='【管理】设置Trend游戏的概率分布，总和必须100')
async def set_trend(interaction: discord.Interaction, mild: int, huge: int, drop: int):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("🚫 你没有权限修改概率！", ephemeral=True)
        return

    if mild + huge + drop != 100:
        await interaction.response.send_message(f"🚫 三个数加起来必须等于100！\n你输入的是: {mild+huge+drop}", ephemeral=True)
        return

    trend_config['mild'] = mild
    trend_config['huge'] = huge
    trend_config['drop'] = drop

    await interaction.response.send_message(
        f"✅ **概率已更新！**\n"
        f"📈 温和上涨 (0~10%): **{mild}%**\n"
        f"🚀 暴力拉升 (10~15%): **{huge}%**\n"
        f"📉 下跌回调 (-8~0%): **{drop}%**\n"
        f"接下来的 /trend 命令将应用此配置。",
        ephemeral=False
    )

if __name__ == '__main__':
    if not TOKEN:
        print('请设置DISCORD_TOKEN环境变量！')
    else:
        bot.run(TOKEN)
