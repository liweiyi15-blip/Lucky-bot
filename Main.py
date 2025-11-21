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

trend_config = {
    "mild": 60,
    "huge": 35,
    "drop": 5
}

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
TOKEN = os.getenv('DISCORD_TOKEN')

@bot.event
async def on_ready():
    print(f'{bot.user} 已上线！')
    try:
        synced = await bot.tree.sync()
        print(f'同步了 {len(synced)} 个slash命令')
    except Exception as e:
        print(e)

# ================= 1. /coin 金币预测 =================
@bot.tree.command(name='coin', description='用好运硬币预测股票涨跌！')
@app_commands.describe(stock="输入你希望被好运祝福的代码", day="选择预测日期")
@app_commands.choices(day=[
    app_commands.Choice(name='今天', value='today'),
    app_commands.Choice(name='明天', value='tomorrow')
])
async def coin(interaction: discord.Interaction, stock: str, day: str):
    stock = stock.upper().strip()
    result = random.choice([0, 1])
    is_up = result == 0
    day_text = '今天' if day == 'today' else '明天'
    
    question = f"**🙏硬币啊~硬币~告诉我{day_text}{stock}是涨还是跌？🙏**"
    embed = discord.Embed(title=question, color=0x3498DB)
    embed.set_image(url='https://i.imgur.com/hXY5B8Z.gif' if is_up else 'https://i.imgur.com/co0MGhu.gif')
    await interaction.response.send_message(embed=embed)

# ================= 2. /buy 命运转盘 (赛博朋克滚轮版) =================
@bot.tree.command(name='buy', description='每日自动热度转盘 + 实时原因，直接转！')
async def buy(interaction: discord.Interaction):
    await interaction.response.defer()
    
    # 1. 获取代码
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

    # === 2. 构造滚轮序列 ===
    # 稍微加长一点序列，保证动画流畅
    full_wheel = all_options * 3 
    
    # 随机截取一段作为动画序列
    # 保证 winner 出现在序列的最后
    # 我们构建一个 list: [乱序... 乱序... winner]
    
    # 先随机跑 10-15 个
    pre_sequence = [random.choice(all_options) for _ in range(random.randint(10, 15))]
    # 确保最后一个不是 winner，避免重复尴尬
    if pre_sequence[-1] == winner:
        pre_sequence[-1] = random.choice([x for x in all_options if x != winner])
        
    spin_sequence = pre_sequence + [winner]

    # 发送初始 Embed
    embed = discord.Embed(title="**🎰 命运大转盘启动**", description="初始化中...", color=0x3498DB)
    embed.set_footer(text="纯娱乐推荐，投资需谨慎👻")
    await interaction.followup.send(embed=embed)

    # === 3. 执行滚动动画 (视窗效果) ===
    # 视窗大小：显示 上一个、当前、下一个
    
    for i in range(len(spin_sequence)):
        # 速度控制：抛物线刹车 (前面快，最后慢)
        total = len(spin_sequence)
        if i < total * 0.7:
            sleep_time = 0.1  # 极速
        elif i < total * 0.9:
            sleep_time = 0.25 # 减速
        else:
            sleep_time = 0.5 + (i - total * 0.9) * 0.2 # 缓慢定格
            
        await asyncio.sleep(sleep_time)
        
        # 获取当前视窗的数据
        curr = spin_sequence[i]
        
        # 计算上一个 (如果是第0个，就随机显示一个作为上一个)
        prev = spin_sequence[i-1] if i > 0 else random.choice(all_options)
        
        # 计算下一个 (如果是最后一个，显示'???')
        if i < len(spin_sequence) - 1:
            nxt = spin_sequence[i+1]
        else:
            nxt = " END "

        # === 核心视觉设计 ===
        # 灰色小字显示上下，中间用一级标题放大
        # 使用代码块包裹上下行，中间行裸奔以获得Markdown大字体效果
        
        view_str = (
            f"```\n   {prev}\n```"
            f"# 👉 {curr} 👈"  # 这里是最大号字体
            f"```\n   {nxt}\n```"
        )
        
        embed.description = view_str
        await interaction.edit_original_response(embed=embed)

    await asyncio.sleep(0.5)

    # === 4. 生成理由 ===
    prompt_reason = f"用一句简要真实的原因总结今天买{winner}的理由，严格20字以内，无迷信"
    try:
        comp = await client.chat.completions.create(
            model="deepseek-chat", messages=[{"role": "user", "content": prompt_reason}], max_tokens=40
        )
        reason = comp.choices[0].message.content.strip()
    except:
        reason = "AI 暂时掉线，但直觉告诉你就是它！"

    # === 5. 最终结果 (高亮版) ===
    if winner in ['不操作', '清仓']:
        action_text = f"今天建议 {winner}"
        color_syntax = "-" # 红色 (diff语法)
    else:
        action_text = f"今天推荐买 {winner}"
        color_syntax = "+" # 绿色 (diff语法)

    # 使用 diff 代码块实现颜色高亮
    final_view = (
        f"# 🎉 命运已定！\n"
        f"```diff\n"
        f"{color_syntax} {action_text}\n"
        f"```\n"
        f"**{reason}**"
    )
    
    embed.description = final_view
    embed.color = 0x2ECC71 if color_syntax == "+" else 0xE74C3C # 绿或红
    embed.set_footer(text="") # 清除脚注
    await interaction.edit_original_response(embed=embed)

# ================= 3. /trend 走势剧本 =================
@bot.tree.command(name='trend', description='占卜预测今日股票走势')
async def trend(interaction: discord.Interaction, stock: str):
    await interaction.response.defer()
    stock = stock.upper().strip()

    # 占卜动画
    embed_loading = discord.Embed(
        title=f"🔮 正在为 {stock} 占卜中...",
        description="✨ *观星象，测运势，连接宇宙能量...*",
        color=0x9B59B6
    )
    message = await interaction.followup.send(embed=embed_loading)

    # 计算
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
    )

    try:
        completion = await client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=80,
            temperature=1.1
        )
        story = completion.choices[0].message.content.strip()
    except:
        story = "AI 信号受到宇宙射线干扰..."

    await asyncio.sleep(3)

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

# ================= 4. /set_trend 设置概率 =================
@app_commands.default_permissions(administrator=True)
@bot.tree.command(name='set_trend', description='【管理】设置概率分布')
async def set_trend(interaction: discord.Interaction, mild: int, huge: int, drop: int):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("🚫 你没有权限！", ephemeral=True)
        return
    if mild + huge + drop != 100:
        await interaction.response.send_message(f"🚫 总和必须100！", ephemeral=True)
        return
    trend_config['mild'] = mild
    trend_config['huge'] = huge
    trend_config['drop'] = drop
    await interaction.response.send_message(f"✅ **配置已更新**", ephemeral=True)

if __name__ == '__main__':
    if not TOKEN:
        print('请设置DISCORD_TOKEN环境变量！')
    else:
        bot.run(TOKEN)
