import { FormEvent, useEffect, useState } from "react";
type Origin = { id: string; label: string; starting_skills: Record<string, number>; starting_items: string[]; contextual_strength: string };
type Campaign = { id: string; name: string; character_name: string; profession: string; attributes: Record<string, number>; skills: Record<string, number>; starting_items: string[]; contextual_strength: string; health: number; hunger: number; thirst: number; fatigue: number };
const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const skillNames: Record<string, string> = { primeiros_socorros: "Primeiros socorros", construcao_reparos: "Construção e reparos", investigacao_sintomas: "Investigação de sintomas", mecanica: "Mecânica", ferramentas_manutencao: "Uso e manutenção de ferramentas" };
const attributeNames: Record<string, string> = { vigor: "Vigor", coordenacao: "Coordenação", percepcao: "Percepção", raciocinio: "Raciocínio", presenca: "Presença" };

export default function App() {
  const [origins, setOrigins] = useState<Origin[]>([]);
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [campaignName, setCampaignName] = useState("Primeira noite");
  const [characterName, setCharacterName] = useState("");
  const [profession, setProfession] = useState("bombeiro");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch(API + "/api/v1/game/origins").then((response) => {
      if (!response.ok) throw new Error("Não foi possível carregar as origens.");
      return response.json() as Promise<Origin[]>;
    }).then((data) => { setOrigins(data); if (data.length) setProfession(data[0].id); })
      .catch((reason: Error) => setError(reason.message));
  }, []);

  async function startCampaign(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setLoading(true); setError("");
    try {
      const response = await fetch(API + "/api/v1/campaigns", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ campaign_name: campaignName, character_name: characterName, profession }) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail ?? "Falha ao criar campanha.");
      setCampaign(data as Campaign);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Erro inesperado."); }
    finally { setLoading(false); }
  }

  if (campaign) return <main className="shell"><header><span className="eyebrow">AMAZONIA · PROTÓTIPO</span><h1>O mundo mudou.</h1></header><section className="panel"><p className="eyebrow">CAMPANHA CRIADA</p><h2>{campaign.name}</h2><p>{campaign.character_name} · {origins.find((item) => item.id === campaign.profession)?.label}</p><div className="stats">{Object.entries(campaign.attributes).map(([key,value]) => <div className="stat" key={key}><span>{attributeNames[key] ?? key}</span><strong>{value}</strong></div>)}</div><h3>Habilidades iniciais</h3><ul>{Object.entries(campaign.skills).map(([key,value]) => <li key={key}>{skillNames[key] ?? key}: nível {value}</li>)}</ul><h3>Equipamentos</h3><ul>{campaign.starting_items.map((item) => <li key={item}>{item.replaceAll("_", " ")}</li>)}</ul><p className="muted">{campaign.contextual_strength}</p><p className="muted">Saúde {campaign.health}/100 · Fome {campaign.hunger}/100 · Sede {campaign.thirst}/100 · Fadiga {campaign.fatigue}/100</p><button onClick={() => setCampaign(null)}>Voltar</button></section></main>;

  return <main className="shell"><header><span className="eyebrow">RPG DE SOBREVIVÊNCIA · BRASIL</span><h1>AMAZONIA</h1><p className="lead">O colapso não aconteceu em um único dia. Sua história começa agora.</p></header><form className="panel" onSubmit={startCampaign}><h2>Iniciar campanha</h2><label>Nome da campanha<input value={campaignName} onChange={(event) => setCampaignName(event.target.value)} maxLength={80} required /></label><label>Nome do personagem<input value={characterName} onChange={(event) => setCharacterName(event.target.value)} maxLength={60} required /></label><label>Experiência de origem<select value={profession} onChange={(event) => setProfession(event.target.value)}>{origins.map((item) => <option value={item.id} key={item.id}>{item.label}</option>)}</select></label>{error && <p className="error" role="alert">{error}</p>}<button disabled={loading || origins.length === 0}>{loading ? "Preparando..." : "Criar personagem"}</button></form><footer>Protótipo de desenvolvimento · Grande São Paulo</footer></main>;
}
