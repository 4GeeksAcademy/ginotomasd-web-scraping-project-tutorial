import os
from bs4 import BeautifulSoup
import requests
import time
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

resource_url = "https://en.wikipedia.org/wiki/List_of_Spotify_streaming_records"

time.sleep(10)
response = requests.get(resource_url)
soup = BeautifulSoup(response.text, 'lxml')

data = pd.read_html(resource_url)
df = data[0]

df = df[~df['Rank'].astype(str).str.contains("As of")].copy()

df['Streams (billions)'] = (
    df['Streams (billions)']
    .astype(str)
    .str.replace('$', '', regex=False)
    .str.replace('B', '', regex=False)
    .astype(float) * 1_000_000_000
)

df.dropna(inplace=True)

df.rename(columns={
    "Artist(s)": "Artist",
    "Streams (billions)": "Streams",
    "Release date": "Release_date"
}, inplace=True)

df['Release_date'] = pd.to_datetime(df['Release_date'], errors='coerce')
df.dropna(subset=['Release_date'], inplace=True)
df['Year'] = df['Release_date'].dt.year
df['Release_date'] = df['Release_date'].astype(str)

con = sqlite3.connect('test.db')
cursor = con.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS spotify_songs (
        Rank INTEGER,
        Song TEXT,
        Artist TEXT,
        Streams REAL,
        Release_date TEXT
    )
''')

cursor.executemany('''
    INSERT INTO spotify_songs (Rank, Song, Artist, Streams, Release_date)
    VALUES (?, ?, ?, ?, ?)
''', df[['Rank', 'Song', 'Artist', 'Streams', 'Release_date']].values.tolist())

con.commit()
con.close()

con = sqlite3.connect('test.db')
cursor = con.cursor()

top_songs = df.sort_values('Streams', ascending=False).head(10)
sns.barplot(data=top_songs, x='Streams', y='Song')
plt.title('Top 10 Most Streamed Songs')
plt.xlabel('Streams')
plt.ylabel('Song')
plt.tight_layout()
plt.show()

streams_by_year = df.groupby('Year')['Streams'].sum().reset_index()
sns.lineplot(data=streams_by_year, x='Year', y='Streams')
plt.title('Total Streams by Release Year')
plt.ylabel('Streams')
plt.tight_layout()
plt.show()

sns.scatterplot(data=df, x='Year', y='Streams')
plt.title('Streams by Release Year')
plt.tight_layout()
plt.show()