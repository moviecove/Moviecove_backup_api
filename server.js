import express from "express";
import fetch from "node-fetch";

const app = express();
const PORT = process.env.PORT || 3000;

const TOKEN = "08166704020_tony_destiny_movie_api";

// Proxy latest movies
app.get("/movies/latest/:page", async (req, res) => {
  try {
    const page = req.params.page;
    const r = await fetch(`https://vidsrc-embed.ru/movies/latest/page-${page}.json`);
    const data = await r.json();
    res.json(data);
  } catch(e) {
    res.status(500).json({error: "Failed to fetch movies"});
  }
});

// Proxy latest TV
app.get("/tv/latest/:page", async (req, res) => {
  try {
    const page = req.params.page;
    const r = await fetch(`https://vidsrc-embed.ru/tvshows/latest/page-${page}.json`);
    const data = await r.json();
    res.json(data);
  } catch(e) {
    res.status(500).json({error: "Failed to fetch TV shows"});
  }
});

// Proxy movie stream
app.get("/stream/movie/:id", async (req,res)=>{
  const id = req.params.id;
  const r = await fetch(`https://vidsrc-embed.ru/embed/movie?tmdb=${id}`);
  const html = await r.text();
  // Your vidsrc extractor logic goes here
  res.json({ playable: true, data: [{stream: "https://playlist.m3u8"}] });
});

// Proxy TV stream
app.get("/stream/tv/:id/:season/:episode", async (req,res)=>{
  const {id, season, episode} = req.params;
  const r = await fetch(`https://vidsrc-embed.ru/embed/tv?tmdb=${id}&season=${season}&episode=${episode}`);
  const html = await r.text();
  // Your vidsrc extractor logic goes here
  res.json({ playable: true, data: [{stream: "https://playlist.m3u8"}] });
});

app.listen(PORT, ()=>console.log(`Server running on port ${PORT}`));
