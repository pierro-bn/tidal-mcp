# tidal-mcp

[![Soutenir sur Ko-fi](https://img.shields.io/badge/Ko--fi-Soutenir%20le%20projet-FF5E5B?logo=ko-fi&logoColor=white)](https://ko-fi.com/pierrobn)

Serveur MCP pour rechercher de la musique et consulter ou organiser une collection TIDAL. Dérivé communautaire de [sickn33/tidal-mcp](https://github.com/sickn33/tidal-mcp), sous licence MIT ; les attributions d'origine sont conservées.

## Installation

Prérequis : **Python 3.11 à 3.13**.

```sh
git clone https://github.com/pierro-bn/tidal-mcp.git
cd tidal-mcp
python -m venv .venv
```

Activez l'environnement avec `.venv\Scripts\Activate.ps1` sous PowerShell ou `source .venv/bin/activate` sous macOS/Linux, puis :

```sh
python -m pip install -e .
tidal-auth
```

Autorisez votre compte avec le lien affiché par `tidal-auth`. Configurez ensuite le client MCP pour lancer l'exécutable installé `tidal-mcp`, ou le Python de cet environnement avec `-m tidal_mcp`. Le transport est **stdio**. L'authentification interactive se fait avant le lancement par le client MCP.

## Fonctionnalités et configuration

Recherche de titres, albums et artistes, consultation des favoris et playlists, recommandations et organisation de la collection. Commencez par `tidal_auth_status` ; utilisez notamment `tidal_search`, `tidal_list_favorite_tracks`, `tidal_list_playlists` et `tidal_get_playlist_tracks`.

| Variable | Valeur par défaut / utilisation |
| --- | --- |
| `TIDAL_MCP_ENABLE_WRITES` | `false` ; `true` autorise les écritures après redémarrage |
| `TIDAL_MCP_DATA_DIR` | Répertoire de données utilisateur de la plateforme, application `tidal-local-mcp` |
| `TIDAL_MCP_SESSION_FILE` | `session.json` dans ce répertoire ; chemin personnalisable |
| `TIDAL_MCP_DRAFT_TTL_SECONDS` | `900` secondes ; valeurs acceptées de 60 à 3600 |

Les écritures sont désactivées par défaut. Une fois activées, l'assistant doit présenter l'aperçu exact, obtenir votre accord, puis appeler `tidal_commit_action` avec le jeton de cet aperçu. Un aperçu expiré doit être recréé. Après un échec dont le résultat est incertain, inspectez la collection avant de préparer un nouvel aperçu.

Exemple : « Propose une playlist à partir de mes favoris et montre-moi son contenu avant de la créer. »

## Réponses compactes et économie de tokens

Les outils de lecture du catalogue, de recherche, de listes et de recommandations acceptent `detail: "compact"` (par défaut) ou `detail: "detailed"`. Le mode compact retire les liens et certaines métadonnées secondaires ; il conserve les identifiants des éléments, titres, artistes, disponibilité lorsqu'elle est présente, pagination et provenance des recommandations. Le mode détaillé restitue la réponse complète.

`tidal_check_favorite_tracks` prend `track_ids` (1 à 100 IDs) et `max_pages` (100 par défaut, de 1 à 200). Il parcourt les favoris côté serveur par pages de 50 et renvoie seulement les candidats : `favorite`, `not_favorite` ou `unknown`. `complete` et `reason` précisent la couverture. Une erreur ou une limite de parcours conserve les correspondances trouvées et laisse les autres inconnues. Le parcours s'arrête aussi lorsque tous les candidats sont trouvés. Il peut nécessiter plusieurs appels TIDAL, même si la réponse à l'assistant reste courte.

Les aperçus, jetons, confirmations et résultats des modifications ne sont pas compactés. L'outil d'authentification reste inchangé.

Les gains dépendent de la taille des résultats et du client MCP ; ce mode ne garantit pas un pourcentage de réduction des tokens.

## Développement

Dans l'environnement activé :

```sh
python -m pip install pytest
python -m pytest
```

## Confidentialité

Ne commitez pas vos clés, jetons, fichiers de session ou exports personnels. Les outils peuvent renvoyer des données du compte connecté au client MCP ; vérifiez ces résultats avant de les partager.

## Changes in this derivative

Authentication and logout success messages omit local filesystem paths and account identifiers. Regression tests verify that successful authentication does not print these values.

Cette version est distribuée sous forme de sources sur GitHub, sans publication npm ou PyPI.

On Windows, local session confidentiality relies on the ACLs of your user-data directory; POSIX mode bits do not enforce owner-only access there. Keep custom storage directories private.

## Claude et ChatGPT

| Client | Connexion proposée |
| --- | --- |
| Claude Desktop | Serveur local MCP sur stdio, configuration ci-dessous |
| Claude Code | Même commande locale, via `claude mcp add` |
| ChatGPT | Serveur local relié par Secure MCP Tunnel, sous réserve d'accès à cette fonction |
| Claude web / mobile | Non fourni ici : exige un serveur MCP distant accessible en HTTPS |

Le dépôt GitHub contient le code, pas un endpoint MCP hébergé. Les tests vérifient l'initialisation et la découverte des outils sur stdio ; ils ne constituent pas une connexion réelle à ton compte Claude ou ChatGPT.

### Claude Desktop

Installe d'abord le projet avec les commandes ci-dessus. Ouvre la configuration MCP de Claude Desktop (`claude_desktop_config.json`) et fusionne cette entrée avec tes serveurs existants :

```json
{
  "mcpServers": {
    "tidal-mcp": {
      "command": "C:/mcp/tidal-mcp/.venv/Scripts/python.exe",
      "args": [
        "-m",
        "tidal_mcp"
      ],
      "env": {
        "TIDAL_MCP_ENABLE_WRITES": "false"
      }
    }
  }
}
```

Un [fichier exemple](examples/claude_desktop_config.example.json) est fourni. Remplace les chemins génériques et les valeurs `REPLACE_…` uniquement dans ta configuration privée. Sous macOS/Linux, utilise le chemin absolu du dépôt et `.venv/bin/python` à la place de `.venv/Scripts/python.exe`. Aucun terminal interactif ne doit être nécessaire au démarrage. Redémarre Claude après modification.

### Claude Code

Après avoir défini les mêmes variables d'environnement dans ton terminal, enregistre la commande avec une portée utilisateur :

```sh
claude mcp add --transport stdio --scope user tidal-mcp -- "C:/mcp/tidal-mcp/.venv/Scripts/python.exe" "-m" "tidal_mcp"
```

Adapte les chemins à ton système ; consulte `claude mcp list`, puis `/mcp` dans Claude Code pour vérifier la connexion. Les secrets du terminal doivent être disponibles lors des lancements suivants ; une configuration d'environnement privée persistante peut être nécessaire.

### ChatGPT — tunnel privé

Installe [tunnel-client](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels), crée un tunnel autorisé pour ton espace et définis localement `CONTROL_PLANE_API_KEY`, ainsi que les variables du serveur.

```sh
tunnel-client init --sample sample_mcp_stdio_local --profile tidal-mcp --tunnel-id REPLACE_WITH_TUNNEL_ID --mcp-command "C:/mcp/tidal-mcp/.venv/Scripts/tidal-mcp.exe"
tunnel-client doctor --profile tidal-mcp --explain
tunnel-client run --profile tidal-mcp
```

Garde ce processus ouvert. Dans ChatGPT : **Plugins → Ajouter un serveur MCP personnalisé → Tunnel**, sélectionne ce tunnel, puis installe le plugin. Ce serveur local ne fournit pas OAuth côté MCP : choisis « Sans authentification » pour cette connexion privée protégée par les droits du tunnel. L'authentification du service reste locale. L'accès dépend des permissions de ton organisation/espace. [Guide officiel](https://developers.openai.com/api/docs/guides/custom-mcp-server).

Les commandes ci-dessus supposent des chemins sans espaces pour la commande encapsulée par le tunnel. Adapte-les ou configure le lancement selon l'aide de `tunnel-client`. Sous macOS/Linux, remplace l'exécutable Python installé par `.venv/bin/tidal-mcp`. Le tunnel donne accès au compte configuré sur cette machine : réserve-le à ton espace de confiance. Il ne transforme pas ce serveur personnel en service multi-utilisateur.

### Session et authentification

Exécute `tidal-auth` dans le même environnement et sous le même utilisateur que le serveur. Vérifie avec `tidal-auth --status`. Pour déconnecter : `tidal-auth --logout --yes`. Garde le fichier de session hors du dépôt. Les écritures restent désactivées ; si tu les actives, chaque action nécessite un aperçu puis ta confirmation.

### Vérification et dépannage

Essaie : « Vérifie mon authentification TIDAL avec tidal_auth_status. » Les résultats des outils et ressources peuvent contenir des données de ton compte ; le client qui les consulte les reçoit. Si le serveur ne démarre pas, vérifie les chemins absolus, l'installation des dépendances et les variables d'environnement. Si ChatGPT ne propose pas ton tunnel, vérifie ses droits et son rattachement à l'espace. Ne renseigne pas l'URL GitHub comme URL de serveur MCP.

Références : [Claude local](https://support.claude.com/en/articles/10949351-getting-started-with-local-mcp-servers-on-claude-desktop), [Claude Code MCP](https://code.claude.com/docs/en/mcp), [connecteurs Claude distants](https://support.claude.com/en/articles/11175166-get-started-with-custom-connectors-using-remote-mcp). Voir ces guides pour les réglages propres à chaque client.

## Soutenir le projet

Si ce serveur MCP vous est utile, vous pouvez soutenir son développement et sa maintenance avec un don facultatif sur [Ko-fi](https://ko-fi.com/pierrobn). Merci pour votre soutien !
