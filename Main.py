import discord
from discord.ext import commands
import random
import os
import asyncio
from discord import app_commands

# DeepSeek 个人API
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
    print(f'{bot.user} 已上线！命运转盘 + 实时点评模式启动~')
    try:
        synced = await bot.tree.sync()
        print(f'同步了 {len(synced)} 个slash命令')
    except Exception as e:
        print(e)

# /lucky 保持不变（略）

# /buy 超级命运转盘（<>只包裹股票代码）
@bot.tree.command(name='buy', description='每日自动热度转盘 + 实时点评，直接转！')
async def buy(interaction: discord.Interaction):
    await interaction.response.defer()

    hot7 = ['TSLA', 'NVDA', 'GOOG', 'XPEV', 'CRCL', 'BABA', 'MU']
    fixed = ['TQQQ', 'SQQQ', 'BTC', 'BABA', 'NIO', 'UVXY', '不操作', '清仓']
    all_options = list(dict.fromkeys(hot7 + fixed))

    winner = random.choice(all_options)

    # 转盘动画（不变）
    full_wheel = all_options * random.randint(2, 3)
    k = random.randint(5, min(15, len(full_wheel)))
    fast_sequence = [full_wheel[i] for i in random.sample(range(len(full_wheel)), k)]

    slow_sequence = []
    for _ in range(random.randint(3, 6)):
        slow_sequence.append(random.choice(all_options))
    slow_sequence.append(winner)
    spin_sequence = fast_sequence + slow_sequence

    embed = discord.Embed(title="**今天买什么？** 🛍️", description="🎰 **大转盘启动中... 转啊转~**", color=0x3498DB)
    embed.set_footer(text="纯娱乐推荐，投资需谨慎👻")
    await interaction.followup.send(embed=embed)

    for i, current in enumerate(spin_sequence):
        await asyncio.sleep(0.2 if i < len(fast_sequence) else 0.5 + (i - len(fast_sequence))*0.1)
        arrow = " **→** " if i < len(spin_sequence)-1 else " **✅**"
        embed.description = f"🎰 **转动中... 当前: {current}{arrow}**"
        await interaction.edit_original_response(embed=embed)

    # 生成一句真实原因（严格25字以内）
    prompt = f"用一句简要真实的原因总结今天{winner}的理由，严格15-25字以内，无迷信"

    completion = await client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=30,
        temperature=0.8
    )
    reason = completion.choices[0].message.content.strip()
    reason = (reason[:25] + '...') if len(reason) > 25 else reason

    # 严格按你要求格式（<>只包裹股票代码）
    if winner in ['不操作', '清仓']:
        final = f"转盘停下！🎉\n今天建议 <**{winner}**>\n（{reason}）"
    else:
        final = f"转盘停下！🎉\n今天推荐买 <**{winner}**>\n（{reason}）"

    embed.description = final
    await interaction.edit_original_response(embed=embed)

if __name__ == '__main__':
    if not TOKEN:
        raise ValueError('请设置DISCORD_TOKEN环境变量！')
    bot.run(TOKEN)
