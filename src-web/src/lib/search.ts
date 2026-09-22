// Servicio cliente para búsqueda web en tiempo real sin requerir APIs de pago
export interface SearchResult {
  title: string;
  url: string;
  snippet: string;
}

export async function searchWeb(query: string): Promise<SearchResult[]> {
  const results: SearchResult[] = [];
  const cleanQuery = query.trim();
  if (!cleanQuery) return results;

  try {
    // Intentamos primero DuckDuckGo Instant Answer API JSON
    const ddgApiUrl = `https://api.duckduckgo.com/?q=${encodeURIComponent(cleanQuery)}&format=json&no_html=1&skip_disambig=1`;
    const res = await fetch(ddgApiUrl);
    if (res.ok) {
      const data = await res.json();
      if (data.AbstractText) {
        results.push({
          title: data.Heading || cleanQuery,
          url: data.AbstractURL || "https://duckduckgo.com/?q=" + encodeURIComponent(cleanQuery),
          snippet: data.AbstractText,
        });
      }

      if (Array.isArray(data.RelatedTopics)) {
        for (const topic of data.RelatedTopics.slice(0, 4)) {
          if (topic.Text && topic.FirstURL) {
            results.push({
              title: topic.Text.slice(0, 60) + "...",
              url: topic.FirstURL,
              snippet: topic.Text,
            });
          }
        }
      }
    }
  } catch (err) {
    console.warn("Fallo en DuckDuckGo API:", err);
  }

  // Si no arrojó abstract o se requiere cobertura de noticias y web general
  if (results.length === 0) {
    try {
      // Usamos Wikipedia REST API abierta en español para hechos/definiciones
      const wikiUrl = `https://es.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(cleanQuery)}`;
      const wikiRes = await fetch(wikiUrl);
      if (wikiRes.ok) {
        const wikiData = await wikiRes.json();
        if (wikiData.extract) {
          results.push({
            title: wikiData.title,
            url: wikiData.content_urls?.desktop?.page || `https://es.wikipedia.org/wiki/${encodeURIComponent(cleanQuery)}`,
            snippet: wikiData.extract,
          });
        }
      }
    } catch (e) {
      // Ignorado
    }
  }

  // Si aún está vacío, construimos resultado directo de búsqueda para referencia
  if (results.length === 0) {
    results.push({
      title: `Búsqueda Web: ${cleanQuery}`,
      url: `https://duckduckgo.com/?q=${encodeURIComponent(cleanQuery)}`,
      snippet: `Consulta web en vivo generada para "${cleanQuery}".`,
    });
  }

  return results;
}
