Ambientes
Padrão do projeto: produção e homologação separadas, desenvolvimento 100% em nuvem.
Ambiente	Banco (Neon)	Região
Homologação	`pos-surto-homologacao`	aws-sa-east-1 (São Paulo)
Produção	`pos-surto-producao`	aws-sa-east-1 (São Paulo)
Regras:
Toda mudança de esquema é validada primeiro na homologação.
Credenciais e strings de conexão nunca entram no repositório; ficam em variáveis de ambiente (ver `.env.example`).
Todo código deve ter cada função documentada e explicada.
