import matplotlib.pyplot as plt
from collections import defaultdict
from functools import lru_cache

def trend_analysis(vectorstore, title: str, start_year: int, end_year: int, min_year=1991, max_year=2025) -> plt.Figure:
    """Trend analysis, plot the trend of number of articles"""

    @lru_cache(maxsize=None) 
    def get_articles_count_by_year():        
        nb_articles = {}
        for year in range(1988,2026):
            results = vectorstore.get(where={"year": str(year)})
            nb_articles[year] = len(results['ids'])
        return nb_articles

    nb_articles = get_articles_count_by_year()

    docs = vectorstore.similarity_search(title, k=5000) 
    yearly_counts = defaultdict(int)
    for doc in docs:
        metadata = doc.metadata  
        if "year" in metadata:
            yearly_counts[int(metadata["year"])] += 1      

    # plot
    years = sorted(yearly_counts.keys())
    counts = [yearly_counts[year]/nb_articles[year] * 100 for year in years]

    fig = plt.figure(figsize=(10, 6))
    plt.plot(years, counts, marker='o', linestyle='-')
    plt.xlabel("Year")
    plt.xlim((max(min_year,start_year), min(end_year, max_year)))
    plt.ylabel(f"% of related articles")
    plt.title(f"Trend of {title} in arXiv's articles ({start_year}-{end_year})")
    plt.grid(True)
    
    return fig


