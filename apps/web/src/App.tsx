import { FormEvent, useEffect, useState } from "react";
import MapView from "./MapView";
import type { InventoryItem, MapData } from "./types";

const API_BASE = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
type Account = { id: string; email: string; display_name: string };
type AuthResponse = { user: Account };

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
  position_q: number;
  position_r: number;
  discovered_cells: string[];
};

type Campaign = {
  id: string;
  name: string;
  status: string;
  world_time_minutes: number;
  character: Character | null;
};

const DIRECTIONS = [
  { label: "N", q: 0, r: -1 },
  { label: "NE", q: 1, r: -1 },
  { label: "SE", q: 1, r: 0 },
  { label: "S", q: 0, r: 1 },
  { label: "SW", q: -1, r: 1 },
  { label: "NW", q: -1, r: 0 },
];

let csrfToken: string | null = null;

async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const method = (init?.method || "GET").toUpperCase();
  const requestCsrfToken = method === "GET" || method === "HEAD" ? null : csrfToken;
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(requestCsrfToken ? { "X-CSRF-Token": requestCsrfToken } : {}),
      ...init?.headers,
    },
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    const detail = payload?.detail;
    throw new Error(typeof detail === "string" ? detail : `Falha na comunicação com a API (${response.status}).`);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

function formatWorldTime(minutes: number): string {
  const hours = Math.floor(minutes / 60).toString().padStart(2, "0");
  const remainder = (minutes % 60).toString().padStart(2, "0");
  return `${hours}h ${remainder}m`;
}

function App() {
  const [origins, setOrigins] = useState<Origin[]>([]);
  const [account, setAccount] = useState<Account | null>(null);
  const [authReady, setAuthReady] = useState(false);
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [savedCampaigns, setSavedCampaigns] = useState<Campaign[]>([]);
  const [itemCatalog, setItemCatalog] = useState<InventoryItem[]>([]);
  const [usingItem, setUsingItem] = useState(false);
  const [resting, setResting] = useState(false);
  const [campaignName, setCampaignName] = useState("Minha primeira campanha");
  const [characterName, setCharacterName] = useState("");
  const [selectedOrigin, setSelectedOrigin] = useState("bombeiro");
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [mapData, setMapData] = useState<MapData | null>(null);
  const [loading, setLoading] = useState(false);
  const [moving, setMoving] = useState(false);
  const [error, setError] = useState("");
  const [apiReady, setApiReady] = useState(false);

  useEffect(() => {
    let active = true;
    apiRequest<{ csrf_token: string }>("/api/v1/auth/csrf")
      .then((csrf) => { csrfToken = csrf.csrf_token; return apiRequest<Account>("/api/v1/auth/me"); })
      .then(async (user) => {
        if (!active) return;
        setAccount(user);
        const [items, _health, catalog, campaigns] = await Promise.all([
          apiRequest<Origin[]>("/api/v1/game/origins"),
          apiRequest<{ status: string }>("/health"),
          apiRequest<InventoryItem[]>("/api/v1/game/items"),
          apiRequest<Campaign[]>("/api/v1/campaigns"),
        ]);
        if (!active) return;
        setOrigins(items);
        setItemCatalog(catalog);
        setSavedCampaigns(campaigns);
        setApiReady(true);
        if (items.length > 0) setSelectedOrigin(items[0].id);
      })
      .catch(() => { if (active) setError(""); })
      .finally(() => { if (active) setAuthReady(true); });
    return () => { active = false; };
  }, []);

  async function handleAuth(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(""); setLoading(true);
    try {
      const path = authMode === "register" ? "/api/v1/auth/register" : "/api/v1/auth/login";
      const payload = authMode === "register" ? { email, password, display_name: displayName } : { email, password };
      const result = await apiRequest<AuthResponse>(path, { method: "POST", body: JSON.stringify(payload) });
      csrfToken = result.csrf_token;
      setAccount(result.user);
      const [items, catalog, campaigns] = await Promise.all([apiRequest<Origin[]>("/api/v1/game/origins"), apiRequest<InventoryItem[]>("/api/v1/game/items"), apiRequest<Campaign[]>("/api/v1/campaigns")]);
      setOrigins(items); setItemCatalog(catalog); setSavedCampaigns(campaigns); setApiReady(true);
      if (items.length > 0) setSelectedOrigin(items[0].id); setPassword("");
    } catch (err) { setError(err instanceof Error ? err.message : "Não foi possível autenticar."); }
    finally { setLoading(false); setAuthReady(true); }
  }

  async function handleLogout() {
    try { await apiRequest<void>("/api/v1/auth/logout", { method: "POST" }); } finally { csrfToken = null; setAccount(null); setCampaign(null); setMapData(null); setSavedCampaigns([]); setApiReady(false); }
  }

  async function handleResumeCampaign(campaignId: string) {
    setError(""); setLoading(true);
    try {
      const loaded = await apiRequest<Campaign>("/api/v1/campaigns/" + campaignId); setCampaign(loaded);
      setMapData(loaded.character ? await apiRequest<MapData>("/api/v1/campaigns/" + campaignId + "/map") : null);
    } catch (err) { setError(err instanceof Error ? err.message : "Não foi possível retomar a campanha."); }
    finally { setLoading(false); }
  }
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
      setSavedCampaigns((current) => [created, ...current]);
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
      const initialMap = await apiRequest<MapData>(`/api/v1/campaigns/${campaign.id}/map`);
      setMapData(initialMap);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível preparar a exploração.");
    } finally {
      setLoading(false);
    }
  }

  async function handleMove(targetQ: number, targetR: number) {
    if (!campaign || !mapData || moving) return;
    setError("");
    setMoving(true);
    try {
      const nextMap = await apiRequest<MapData>(`/api/v1/campaigns/${campaign.id}/move`, {
        method: "POST",
        body: JSON.stringify({ target_q: targetQ, target_r: targetR }),
      });
      setMapData(nextMap);
      setCampaign({
        ...campaign,
        character: campaign.character
          ? { ...campaign.character, needs: nextMap.character_needs }
          : null,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Movimento não permitido.");
    } finally {
      setMoving(false);
    }
  }

  async function handleUseItem(itemId: string) {
    if (!campaign || !campaign.character || usingItem) return;
    setError("");
    setUsingItem(true);
    try {
      const result = await apiRequest<{
        inventory: string[];
        needs: Record<string, number>;
        world_time_minutes: number;
      }>(`/api/v1/campaigns/${campaign.id}/inventory/use`, {
        method: "POST",
        body: JSON.stringify({ item_id: itemId }),
      });
      setCampaign({
        ...campaign,
        world_time_minutes: result.world_time_minutes,
        character: {
          ...campaign.character,
          inventory: result.inventory,
          needs: result.needs,
        },
      });
      setMapData(mapData ? { ...mapData, world_time_minutes: result.world_time_minutes, character_needs: result.needs } : null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível consumir o item.");
    } finally {
      setUsingItem(false);
    }
  }

  async function handleRest() {
    if (!campaign || !campaign.character || resting || usingItem || moving) return;
    setError("");
    setResting(true);
    try {
      const result = await apiRequest<{
        needs: Record<string, number>;
        world_time_minutes: number;
      }>(`/api/v1/campaigns/${campaign.id}/rest`, { method: "POST" });
      setCampaign({
        ...campaign,
        world_time_minutes: result.world_time_minutes,
        character: { ...campaign.character, needs: result.needs },
      });
      setMapData(mapData ? { ...mapData, world_time_minutes: result.world_time_minutes, character_needs: result.needs } : null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível descansar.");
    } finally {
      setResting(false);
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
        <div className="connection"><span className={apiReady ? "status-dot online" : "status-dot"} />{account ? account.display_name : apiReady ? "SISTEMA CONECTADO" : "SISTEMA AMAZONIA"}{account && <button className="logout-button" type="button" onClick={handleLogout}>SAIR</button>}</div>
      </header>

      <section className="hero">
        <div className="eyebrow"><span /> GRANDE SÃO PAULO · DIA ZERO</div>
        <h1>O mundo como<br /><em>você conhecia</em> acabou.</h1>
        <p>As comunicações caíram. As ruas mudaram. Cada decisão tem um custo. Sua história começa agora.</p>
      </section>

      {error && <div className="error-banner" role="alert">{error}</div>}

      {!authReady ? (<section className="setup-card"><h2>Preparando sua sessão</h2></section>) : !account ? (<section className="setup-card">
          <div className="section-kicker">ACESSO SEGURO · AMAZONIA</div>
          <h2>{authMode === "login" ? "Entre na sua conta" : "Crie sua conta"}</h2>
          <p className="muted">Suas campanhas ficam privadas e vinculadas à sua conta.</p>
          <form onSubmit={handleAuth}>
            {authMode === "register" && <><label htmlFor="display-name">Nome de exibição</label><input id="display-name" value={displayName} onChange={(event) => setDisplayName(event.target.value)} minLength={2} maxLength={80} required /></>}
            <label htmlFor="account-email">E-mail</label>
            <input id="account-email" type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
            <label htmlFor="account-password">Senha {authMode === "register" && "(mínimo 12 caracteres)"}</label>
            <input id="account-password" type="password" autoComplete={authMode === "login" ? "current-password" : "new-password"} minLength={authMode === "register" ? 12 : 1} maxLength={128} value={password} onChange={(event) => setPassword(event.target.value)} required />
            <button className="primary-button" type="submit" disabled={loading}>{loading ? "AGUARDE..." : authMode === "login" ? "ENTRAR" : "CRIAR CONTA"} <span>↗</span></button>
          </form>
          <button className="auth-switch" type="button" onClick={() => setAuthMode(authMode === "login" ? "register" : "login")}>{authMode === "login" ? "Ainda não tem conta? Criar conta" : "Já tem conta? Entrar"}</button>
          <div className="footnote">SENHAS PROTEGIDAS · CAMPANHAS PRIVADAS · SESSÃO COM VALIDADE LIMITADA</div>
        </section>) : !campaign ? (
        <section className="setup-card">
          <div className="section-kicker">01 / INÍCIO DA JORNADA</div>
          <h2>Prepare sua campanha</h2>
          <p className="muted">Dê um nome à sua jornada. O mundo será salvo para você continuar depois.</p>
          {savedCampaigns.length > 0 && <div className="saved-campaigns"><div className="section-kicker">CONTINUAR JORNADA</div>{savedCampaigns.map((saved) => <button key={saved.id} type="button" className="saved-campaign" onClick={() => handleResumeCampaign(saved.id)} disabled={loading}><span><strong>{saved.name}</strong><small>{saved.character ? saved.character.name : "Personagem ainda não criado"} · {formatWorldTime(saved.world_time_minutes)}</small></span><b>RETOMAR ↗</b></button>)}</div>}
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
            <button className="rest-button" type="button" disabled={resting || usingItem || moving} onClick={handleRest}>{resting ? "DESCANSANDO..." : "DESCANSAR · 1 HORA"}</button>
            <div className="section-kicker lower">INVENTÁRIO</div>
            <div className="inventory-list">
              {itemCatalog.filter((item) => campaign.character?.inventory.includes(item.id)).map((item) => {
                const quantity = campaign.character?.inventory.filter((id) => id === item.id).length || 0;
                return (
                  <div className="inventory-row" key={item.id}>
                    <div><strong>{item.label} <span>×{quantity}</span></strong><small>{item.description}</small></div>
                    <button type="button" disabled={usingItem} onClick={() => handleUseItem(item.id)}>USAR</button>
                  </div>
                );
              })}
              {campaign.character.inventory.length === 0 && <p className="muted">Seu inventário está vazio.</p>}
            </div>
          </article>
          <article className="map-card">
            <div className="section-kicker">MAPA DE EXPLORAÇÃO · GRADE HEXAGONAL</div>
            <MapView mapData={mapData} onMove={handleMove} />
            {mapData && (
              <>
                <div className="map-meta">
                  <span>CÉLULA {mapData.player_position.q}:{mapData.player_position.r}</span>
                  <span>TEMPO DO MUNDO {formatWorldTime(mapData.world_time_minutes)}</span>
                  <span>LOCAIS DESCOBERTOS {mapData.points_of_interest.length}</span>
                </div>
                <div className="move-controls" aria-label="Mover para célula adjacente">
                  {DIRECTIONS.map((direction) => (
                    <button
                      key={direction.label}
                      type="button"
                      disabled={moving}
                      onClick={() => handleMove(mapData.player_position.q + direction.q, mapData.player_position.r + direction.r)}
                    >
                      {direction.label}
                    </button>
                  ))}
                </div>
                <div className="map-legend">
                  <span><i className="legend-current" /> POSIÇÃO ATUAL</span>
                  <span><i className="legend-known" /> DESCOBERTO</span>
                  <span><i className="legend-unknown" /> NÃO EXPLORADO</span>
                </div>
              </>
            )}
            <div className="map-note">Cada movimento válido avança 10 minutos. Pontos de interesse só aparecem após descobrir a célula correspondente. Nenhum GPS é solicitado; os dados reais entram pelo processo de importação documentado.</div>
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
