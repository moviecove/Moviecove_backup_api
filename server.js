// server.js
import express from "express";
import fetch from "node-fetch";
import cheerio from "cheerio";
import cors from "cors";

const app = express();
const PORT = process.env.PORT || 3000;
const API_KEY = process.env.MOVIE_API_KEY || "08166704020_tony_destiny_movie_api";

// Enable CORS for all frontends
app.use(cors());

// Middleware: check Bearer token
app.use((req, res, next) => {
  const auth = req.headers.authorization;
  if (!auth || auth !== `Bearer ${API_KEY}`) {
    return res.status(401).json({ error: "Unauthorized" });
  }
  next();
});

// ===== Movie stream endpoint =====
app.get("/stream/movie/:id", async (req, res) => {
  const { id } = req.params;
  try {
    const embedUrl = `https://vidsrc-embed.ru/embed/movie/${id}`;
    const html = await (await fetch(embedUrl)).text();
    const $ = cheerio.load(html);
    const streamUrl = $('source[type="application/x-mpegURL"]').attr("src");

    if (!streamUrl) return res.status(404).json({ playable: false });

    res.json({ playable: true, data: [{ stream: streamUrl }] });
  } catch (err) {
    res.status(500).json({ playable: false, error: err.message });
  }
});

// ===== TV episode stream endpoint =====
app.get("/stream/tv/:id/:season/:episode", async (req, res) => {
  const { id, season, episode } = req.params;
  try {
    const embedUrl = `https://vidsrc-embed.ru/embed/tv/${id}/season-${season}-episode-${episode}`;
    const html = await (await fetch(embedUrl)).text();
    const $ = cheerio.load(html);
    const streamUrl = $('source[type="application/x-mpegURL"]').attr("src");

    if (!streamUrl) return res.status(404).json({ playable: false });

    res.json({ playable: true, data: [{ stream: streamUrl }] });
  } catch (err) {
    res.status(500).json({ playable: false, error: err.message });
  }
});

// ===== List all episodes in a season =====
app.get("/stream/tv/:id/:season", async (req, res) => {
  const { id, season } = req.params;
  try {
    const embedUrl = `https://vidsrc-embed.ru/embed/tv/${id}/season-${season}`;
    const html = await (await fetch(embedUrl)).text();
    const $ = cheerio.load(html);

    const episodes = [];
    $('a[data-episode]').each((i, el) => {
      const epNum = $(el).data('episode');
      const epUrl = $(el).attr('href');
      if (epNum && epUrl) episodes.push({ episode: epNum, embedUrl: epUrl });
    });

    const results = [];
    for (const ep of episodes.slice(0, 10)) { // limit first 10 episodes
      const epHtml = await (await fetch(ep.embedUrl)).text();
      const $ep = cheerio.load(epHtml);
      const streamUrl = $ep('source[type="application/x-mpegURL"]').attr("src");
      if (streamUrl) results.push({ episode: ep.episode, stream: streamUrl });
    }

    if (results.length === 0) return res.status(404).json({ playable: false });
    res.json({ playable: true, data: results });
  } catch (err) {
    res.status(500).json({ playable: false, error: err.message });
  }
});

// ===== Start server =====
app.listen(PORT, () => console.log(`VidSrc backend running on port ${PORT}`));