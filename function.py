from pydantic import Field
from fastmcp import FastMCP
import requests
import os
from typing import Optional
from collections import Counter
from datetime import datetime, timezone, timedelta


mcp = FastMCP(name="github_info_mcp")
BEIJING_TZ = timezone(timedelta(hours=8))

# Get GitHub token from environment variable
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

@mcp.tool
def get_github_clones(repo: Optional[str]=Field("repo_name",description="The repository to get the clones")) -> dict:
    """用户输入github仓库名,调用github官方api接口进行查询,返回github仓库的克隆数数据,
    包含时间与克隆总克隆数与唯一克隆者数据,数据量为近14天内的记录,返回数据为json格式
    """

    url = f"https://api.github.com/repos/{repo}/traffic/clones"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


@mcp.tool
def get_github_views(repo: Optional[str]=Field("repo_name",description="The repository to get the views")) -> dict:
    """用户输入github仓库名,调用github官方api接口进行查询,返回github仓库的访客数,
    包含时间与访问数量与唯一到访者数据,数据量为近14天内的记录,返回数据为json格式
    """

    url = f"https://api.github.com/repos/{repo}/traffic/views"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


@mcp.tool
def get_github_stars(repo: Optional[str] = Field("repo_name", description="The repository to get the stars")) -> dict:
    """
    用户输入github仓库名,调用github官方api接口进行查询,返回github仓库的star用户信息,
    包含时间与star用户的信息,数据量为整个仓库的所有信息,返回数据为json格式,该tool将通过对接口返回数据,得到该仓库stars的具体信息
    """
    headers = {
        "Accept": "application/vnd.github.star+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    all_stargazers = []
    page = 1
    per_page = 100 
    
    while True:
        url = f"https://api.github.com/repos/{repo}/stargazers?per_page={per_page}&page={page}"
        response = requests.get(url, headers=headers)
        
        # 处理 HTTP 错误（如 404、403）
        if response.status_code == 404:
            return {"error": f"Repository '{repo}' not found."}
        elif response.status_code == 403:
            return {"error": "API rate limit exceeded or token invalid."}
        response.raise_for_status()
        
        data = response.json()
        if not data:  
            break
            
        all_stargazers.extend(data)
        print(f"Fetched page {page}, total so far: {len(all_stargazers)}")  
        page += 1
        
    dates = []
    for item in all_stargazers:
        try:
            
            starred_at = item["starred_at"].rstrip("Z")
            date_obj = datetime.fromisoformat(starred_at).date()
            dates.append(str(date_obj))  
        except (KeyError, ValueError) as e:
            continue  

    daily_counts = Counter(dates)
    daily_stars = [
        {"date": date, "star_count": count}
        for date, count in sorted(daily_counts.items())
    ]
    
    return {
        "total_stars_fetched": len(all_stargazers),
        "daily_stars": daily_stars
    }

@mcp.tool
def calculate_rate(
    star: Optional[int] = Field(None, description="someday stars"),
    clones: Optional[int] = Field(None, description="someday clones"),
    views: Optional[int] = Field(None, description="someday views"),
    unique_visitors: Optional[int] = Field(None, description="someday visitors"),
    unique_cloners: Optional[int] = Field(None, description="someday cloners")) -> dict:
    """
    该工具用于计算一些数据的比,具体来说分为了star/clone, star/view, star/visitors, star/cloner, 
    详细解释就是那一天的star数和克隆数、浏览数、唯一浏览者与唯一克隆者的比值,该工具的数据来源主要是get_github_clones、get_github_views
    与get_github_stars这几个工具得到的数据,这些工具都有明确的时间标记,可以便于统计
    """

    if star is None or star == 0:
        return {"error": "star 参数必须提供且大于 0"}

    result = {"star": star}

    def safe_divide(numerator, denominator):
        if denominator in (None, 0):
            return None
        return round(numerator / denominator, 4)

    if clones is not None:
        result["star_per_clone"] = safe_divide(star, clones)
    if views is not None:
        result["star_per_view"] = safe_divide(star, views)
    if unique_visitors is not None:
        result["star_per_unique_visitor"] = safe_divide(star, unique_visitors)
    if unique_cloners is not None:
        result["star_per_unique_cloner"] = safe_divide(star, unique_cloners)

    return result

if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=3001)

