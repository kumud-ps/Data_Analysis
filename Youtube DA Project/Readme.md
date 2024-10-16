**YouTube Data Analysis Project :**

**Overview**
This project involves analyzing YouTube data to uncover insights regarding various metrics like video likes, views, comments, and more. The project leverages Python and libraries such as pandas, seaborn, and matplotlib to visualize trends and relationships in the data.

**Objectives**
Analyze YouTube video data to understand user engagement.
Visualize patterns in video likes, views, and other key metrics.
Implement statistical and exploratory data analysis techniques.


**Project Setup**
**Prerequisites**
Ensure you have the following installed:

Python 3.x
Jupyter Notebook
Required libraries:
pandas
matplotlib
seaborn
numpy

**Dataset**
The dataset contains the following fields (adjust according to your actual dataset):

video_id: Unique identifier for each video.
title: Title of the YouTube video.
channel_title: Title of the channel.
views: Number of views the video received.
likes: Number of likes the video received.
dislikes: Number of dislikes the video received.
comment_count: Number of comments on the video.
published_at: Date the video was published.


**Data Cleaning**
Before starting the analysis, the dataset is cleaned by removing null values, correcting data types, and addressing outliers.

**Exploratory Data Analysis (EDA)**

**1. Video Likes Distribution**

Visualizing the distribution of video likes to understand how this metric is spread across different videos.

python code
plt.figure(figsize=(10,6))
sns.histplot(df['likes'], kde=True)
plt.title('Distribution of Likes')
plt.show()

**2. Relationship Between Views and Likes**
Exploring the correlation between views and likes.

python code
plt.figure(figsize=(10,6))
sns.scatterplot(x='views', y='likes', data=df)
plt.title('Views vs. Likes')
plt.show()

**3. Punctuation in Titles and Likes**
Examining how the number of punctuations in video titles correlates with likes.

python code
df['count_punctuation'] = df['title'].apply(lambda x: sum([1 for c in x if c in string.punctuation]))
plt.figure(figsize=(8,6))
sns.boxplot(x='count_punctuation', y='likes', data=df)
plt.title('Punctuation Count in Titles vs Likes')
plt.show()

**Results and Insights**
**Likes Distribution:** The number of likes follows a right-skewed distribution, with many videos having relatively few likes.
**Views vs. Likes:** There is a positive correlation between views and likes, indicating higher engagement for more viewed content.
**Punctuation Analysis:** There appears to be a mild relationship between punctuation usage in titles and the number of likes, though further analysis may be needed.
**Conclusion**
This project successfully analyzes YouTube data to provide insights into video popularity metrics such as views, likes, and engagement. These insights can help content creators understand trends in viewer engagement and optimize their content strategies.

**Future Work**
Explore other metrics like watch time and user demographics.
Apply machine learning algorithms to predict video popularity.
Perform time-series analysis to track performance over time.
