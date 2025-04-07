import matplotlib.pyplot as plt
from collections import defaultdict

def trend_analysis(vectorstore, title: str, start_year: int, end_year: int) -> None:
    """Trend analysis, plot the trend of number of articles"""
    docs = vectorstore.similarity_search(title, k=5000) 

    yearly_counts = defaultdict(int)
    for doc in docs:
        metadata = doc.metadata  
        if "year" in metadata:
            yearly_counts[int(metadata["year"])] += 1

    # plot
    years = sorted(yearly_counts.keys())
    counts = [yearly_counts[year] for year in years]

    fig = plt.figure(figsize=(10, 6))
    plt.plot(years, counts, marker='o', linestyle='-')
    plt.xlabel("Year")
    plt.xlim((start_year, end_year))
    plt.ylabel("Number of articles")
    plt.title(f"Trend of {title} in arXiv's articles ({start_year}-{end_year})")
    plt.grid(True)
    
    return fig


