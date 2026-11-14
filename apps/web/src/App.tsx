import { FormEvent, useEffect, useState } from "react";
import MapView from "./MapView";

const API_BASE = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

type Origin = {
  id: string;
  label: string;
  starting_skills: Record<string, number>;
  starting_items: string[];
  contextual_strength: string;
};

type Character = {
  id: string;
  campaign_id: string;
  name: string;
  origin: string;
  attributes: Record<string, number>;
  skills: Record<string, number>;
  inventory: string[];
  needs: Record<string, number>;
};

type Campaign = {
  id: string;
  name: string;
  status: string;
  world_time_minutes: number;
  character: Character | null;
};

async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    const detail = payload?.detail;
    throw new Error(typeof detail === "string" ? detail : `Falha na comunicação com a API (${response.status}).`);
  }
  return response.json() as Promise<T>;
}

function App() {
  const [origins, setOrigins] = useState<Origin[]>([]);
  const [campaignName, setCampaignName] = useState("Minha primeira campanha");
  const [characterName, setCharacterName] = useState("");
  const [selectedOrigin, setSelectedOrigin] = useState("bombeiro");
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [apiReady, setApiReady] = useState(false);

  useEffect(() => {
    let active = true;
    Promise.all([
      apiRequest<Origin[]>("/api/v1/game/origins"),
      apiRequest<{ status: string }>("/health"),
    ])
      .then(([items]) => {
        if (!active) return;
        setOrigins(items);
        setApiReady(true);
        if (items.length > 0) setSelectedOrigin(items[0].id);
      })
      .catch(() => {
        if (active) setError("Não foi possível conectar à API. Inicie o backend e atualize a página.");
      });
    return () => { active = false; };
  }, []);

  async function handleCreateCampaign(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const created = await apiRequest<Campaign>("/api/v1/campaigns", {
        method: "POST",
        body: JSON.stringify({ name: campaignName }),
      });
      setCampaign(created);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível criar a campanha.");
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateCharacter(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!campaign) return;
    setError("");
    setLoading(true);
    try {
      const character = await apiRequest<Character>(`/api/v1/campaigns/${campaign.id}/character`, {
        method: "POST",
        body: JSON.stringify({ name: characterName, origin: selectedOrigin }),
      });
      setCampaign({ ...campaign, character });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível criar o personagem.");
    } finally {
      setLoading(false);
    }
  }

  const chosenOrigin = origins.find((origin) => origin.id === selectedOrigin);

  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="Amazonia início">
          <span className="brand-mark">A</span>
          <span>AMAZONIA<small>UM RPG DE SOBREVIVÊNCIA</small></span>
        </a>
        <div className="connection"><span className={apiReady ? "status-dot online" : "status-dot"} />{apiReady ? "SISTEMA CONECTADO" : "CONECTANDO AO SISTEMA"}</div>
      </header>

      <section className="hero">
        <div className="eyebrow"><span /> GRANDE SÃO PAULO · DIA ZERO</div>
        <h1>O mundo como<br /><em>você conhecia</em> acabou.</h1>
        <p>As comunicações caíram. As ruas mudaram. Cada decisão tem um custo. Sua história começa agora.</p>
      </section>

      {error && <div className="error-banner" role="alert">{error}</div>}

      {!campaign ? (
        <section className="setup-card">
          <div className="section-kicker">01 / INÍCIO DA JORNADA</div>
          <h2>Prepare sua campanha</h2>
          <p className="muted">Dê um nome à sua jornada. O mundo será salvo para você continuar depois.</p>
          <form onSubmit={handleCreateCampaign}>
            <label htmlFor="campaign-name">Nome da campanha</label>
            <input id="campaign-name" value={campaignName} onChange={(event) => setCampaignName(event.target.value)} minLength={2} maxLength={80} required />
            <button className="primary-button" type="submit" disabled={loading || !apiReady}>{loading ? "CRIANDO..." : "INICIAR CAMPANHA"} <span>↗</span></button>
          </form>
          <div className="footnote">MODO INDIVIDUAL · PROGRESSO PERSISTENTE · SEM MULTIPLAYER NESTA FASE</div>
        </section>
      ) : !campaign.character ? (
        <section className="setup-card">
          <div className="section-kicker">02 / QUEM VOCÊ É</div>
          <h2>Escolha sua origem</h2>
          <p className="muted">Sua experiência anterior oferece vantagens iniciais, mas não limita o que você poderá aprender.</p>
          <form onSubmit={handleCreateCharacter}>
            <label htmlFor="character-name">Nome do personagem</label>
            <input id="character-name" value={characterName} onChange={(event) => setCharacterName(event.target.value)} minLength={2} maxLength={80} placeholder="Como as pessoas chamam você?" required />
            <label htmlFor="origin">Experiência de origem</label>
            <select id="origin" value={selectedOrigin} onChange={(event) => setSelectedOrigin(event.target.value)}>
              {origins.map((origin) => <option key={origin.id} value={origin.id}>{origin.label}</option>)}
            </select>
            {chosenOrigin && (
              <div className="origin-preview">
                <div><span className="preview-label">VANTAGEM CONTEXTUAL</span><strong>{chosenOrigin.contextual_strength}</strong></div>
                <div><span className="preview-label">HABILIDADES INICIAIS</span><strong>{Object.entries(chosenOrigin.starting_skills).map(([skill, level]) => `${skill.replaceAll("_", " ")} · Nv. ${level}`).join(" / ")}</strong></div>
                <div><span className="preview-label">EQUIPAMENTO INICIAL</span><strong>{chosenOrigin.starting_items.map((item) => item.replaceAll("_", " ")).join(", ")}</strong></div>
              </div>
            )}
            <button className="primary-button" type="submit" disabled={loading}>{loading ? "PREPARANDO..." : "CRIAR PERSONAGEM"} <span>↗</span></button>
          </form>
          <div className="footnote">CAMPANHA: {campaign.name.toUpperCase()}</div>
        </section>
      ) : (
        <section className="game-grid">
          <article className="status-card">
            <div className="section-kicker">CAMPANHA ATIVA</div>
            <h2>{campaign.name}</h2>
            <p className="muted">Sua jornada está criada e salva.</p>
            <div className="character-heading"><div className="avatar">{campaign.character.name.slice(0, 1).toUpperCase()}</div><div><strong>{campaign.character.name}</strong><span>{origins.find((item) => item.id === campaign.character?.origin)?.label || campaign.character.origin}</span></div></div>
            <div className="stat-list">
              {Object.entries(campaign.character.attributes).map(([key, value]) => <div className="stat-row" key={key}><span>{key.toUpperCase()}</span><strong>{value}/5</strong><div className="stat-track"><i style={{ width: `${value * 20}%` }} /></div></div>)}
            </div>
            <div className="section-kicker lower">CONDIÇÕES</div>
            <div className="condition-grid">
              <div><span>SAÚDE</span><strong>{campaign.character.needs.health}%</strong></div>
              <div><span>FOME</span><strong>{campaign.character.needs.hunger}%</strong></div>
              <div><span>SEDE</span><strong>{campaign.character.needs.thirst}%</strong></div>
              <div><span>FADIGA</span><strong>{campaign.character.needs.fatigue}%</strong></div>
            </div>
          </article>
          <article className="map-card">
            <div className="section-kicker">MAPA DE EXPLORAÇÃO</div>
            <MapView />
            <div className="map-note">Mapa de referência centralizado na cidade de São Paulo. A posição inicial do personagem ainda não foi definida; nenhum GPS é solicitado. Os tiles públicos do OpenStreetMap são usados apenas no protótipo de desenvolvimento, com atribuição visível.</div>
          </article>
          <article className="story-card">
            <div className="section-kicker">DIÁRIO DE SOBREVIVÊNCIA</div>
            <h2>O primeiro silêncio</h2>
            <p>O telefone perdeu o sinal há horas. Do lado de fora, sirenes distantes cortam o silêncio — uma depois da outra, até que também desaparecem.</p>
            <p>Você está no começo de uma história que ainda não compreende. Antes de sair, observe o que tem ao seu redor e decida com cuidado.</p>
            <div className="story-rule">O MESTRE DE IA ENTRARÁ QUANDO AS REGRAS E O ESTADO DO MUNDO ESTIVEREM PRONTOS.</div>
          </article>
        </section>
      )}

      <footer><span>AMAZONIA © 2026</span><span>UM MUNDO VIVO. ESCOLHAS REAIS. CONSEQUÊNCIAS PERMANENTES.</span></footer>
    </main>
  );
}

export default App;
