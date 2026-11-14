import { FormEvent, useEffect, useState } from "react";

type Origin = {
  id: string;
  label: string;
  starting_skills: Record<string, number>;
  starting_items: string[];
  contextual_strength: string;
};
type Campaign = {
  id: string;
  name: string;
  status: string;
  world_time_minutes: number;
  character: Character | null;
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

const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const skillNames: Record<string, string> = {
  primeiros_socorros: "Primeiros socorros",
  construcao_reparos: "Construção e reparos",
  investigacao_sintomas: "Investigação de sintomas",
  mecanica: "Mecânica",
  ferramentas_manutencao: "Uso e manutenção de ferramentas",
};
const attributeNames: Record<string, string> = {
  vigor: "Vigor",
  coordenacao: "Coordenação",
  percepcao: "Percepção",
  raciocinio: "Raciocínio",
  presenca: "Presença",
};

export default function App() {
  const [origins, setOrigins] = useState<Origin[]>([]);
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [characterName, setCharacterName] = useState("");
  const [campaignName, setCampaignName] = useState("Primeira noite");
  const [origin, setOrigin] = useState("bombeiro");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch(API + "/api/v1/game/origins")
      .then((response) => {
        if (!response.ok) throw new Error("Não foi possível carregar as origens.");
        return response.json() as Promise<Origin[]>;
      })
      .then((data) => {
        setOrigins(data);
        if (data.length > 0) setOrigin(data[0].id);
      })
      .catch((reason: Error) => setError(reason.message));
  }, []);

  async function startCampaign(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const campaignResponse = await fetch(API + "/api/v1/campaigns", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: campaignName }),
      });
      const campaignData = await campaignResponse.json();
      if (!campaignResponse.ok) {
        throw new Error(campaignData.detail ?? "Não foi possível criar a campanha.");
      }

      const characterResponse = await fetch(
        API + "/api/v1/campaigns/" + campaignData.id + "/character",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name: characterName, origin }),
        },
      );
      const characterData = await characterResponse.json();
      if (!characterResponse.ok) {
        throw new Error(characterData.detail ?? "Não foi possível criar o personagem.");
      }
      setCampaign({ ...campaignData, character: characterData });
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Erro inesperado.");
    } finally {
      setLoading(false);
    }
  }

  if (campaign?.character) {
    const character = campaign.character;
    return (
      <main className="shell">
        <header>
          <span className="eyebrow">AMAZONIA · GRANDE SÃO PAULO</span>
          <h1>O mundo mudou.</h1>
          <p className="lead">Sua jornada começou. Cada escolha terá um custo.</p>
        </header>
        <section className="panel">
          <p className="eyebrow">CAMPANHA CRIADA</p>
          <h2>{campaign.name}</h2>
          <p>{character.name} · {origins.find((item) => item.id === character.origin)?.label}</p>
          <h3>Atributos</h3>
          <div className="stats">
            {Object.entries(character.attributes).map(([key, value]) => (
              <div className="stat" key={key}>
                <span>{attributeNames[key] ?? key}</span><strong>{value}</strong>
              </div>
            ))}
          </div>
          <h3>Habilidades iniciais</h3>
          <ul>
            {Object.entries(character.skills).map(([key, value]) => (
              <li key={key}>{skillNames[key] ?? key}: nível {value}</li>
            ))}
          </ul>
          <h3>Equipamentos</h3>
          <ul>{character.inventory.map((item) => <li key={item}>{item.replaceAll("_", " ")}</li>)}</ul>
          <p className="muted">Saúde {character.needs.health}/100 · Fome {character.needs.hunger}/100 · Sede {character.needs.thirst}/100 · Fadiga {character.needs.fatigue}/100</p>
          <button onClick={() => setCampaign(null)}>Voltar</button>
        </section>
      </main>
    );
  }

  return (
    <main className="shell">
      <header>
        <span className="eyebrow">RPG DE SOBREVIVÊNCIA · BRASIL</span>
        <h1>AMAZONIA</h1>
        <p className="lead">O colapso não aconteceu em um único dia. Sua história começa agora.</p>
      </header>
      <form className="panel" onSubmit={startCampaign}>
        <h2>Iniciar campanha</h2>
        <label>
          Nome da campanha
          <input value={campaignName} onChange={(event) => setCampaignName(event.target.value)} minLength={2} maxLength={80} required />
        </label>
        <label>
          Nome do personagem
          <input value={characterName} onChange={(event) => setCharacterName(event.target.value)} minLength={2} maxLength={80} required />
        </label>
        <label>
          Experiência de origem
          <select value={origin} onChange={(event) => setOrigin(event.target.value)}>
            {origins.map((item) => <option value={item.id} key={item.id}>{item.label}</option>)}
          </select>
        </label>
        {error && <p className="error" role="alert">{error}</p>}
        <button disabled={loading || origins.length === 0}>
          {loading ? "Preparando..." : "Criar personagem"}
        </button>
      </form>
      <footer>Protótipo de desenvolvimento · A campanha é salva no servidor.</footer>
    </main>
  );
}
