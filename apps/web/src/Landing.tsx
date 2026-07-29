import { useEffect, useRef, useState, type MouseEvent as RMouseEvent, type ReactNode } from "react";
import { Link } from "react-router-dom";
import logo from "./assets/logo.png";
import "./landing.css";

type Lang = "pt" | "en";

/* ---------------- ícones (SVG, sem emojis) ---------------- */
type IconProps = { className?: string };
const S = 2.2;
const Svg = (p: { className?: string; children: ReactNode; fill?: string }) => (
  <svg className={p.className} viewBox="0 0 24 24" fill={p.fill ?? "none"} stroke={p.fill ? "none" : "currentColor"}
    strokeWidth={S} strokeLinecap="round" strokeLinejoin="round" aria-hidden>{p.children}</svg>
);
const IcBook =({ className }: IconProps) => (<Svg className={className}><path d="M12 6c-2-1.4-4.5-1.6-7-1v12c2.5-.6 5-.4 7 1 2-1.4 4.5-1.6 7-1V5c-2.5-.6-5-.4-7 1z" /><path d="M12 6v13" /></Svg>);
const IcStar = ({ className }: IconProps) => (<svg className={className} viewBox="0 0 24 24" fill="currentColor" aria-hidden><path d="M12 2.6l2.7 5.7 6.3.8-4.6 4.3 1.2 6.2L12 16.9 6.4 19.6l1.2-6.2L3 9.1l6.3-.8L12 2.6z" /></svg>);
const IcGift = ({ className }: IconProps) => (<Svg className={className}><rect x="3.5" y="10" width="17" height="10.5" rx="1.6" /><path d="M3 10h18M12 10v10.5" /><path d="M12 10S9 5.5 7 6.5 8.5 10 12 10zM12 10s3-4.5 5-3.5S15.5 10 12 10z" /></Svg>);
const IcHeart = ({ className }: IconProps) => (<Svg className={className}><path d="M12 20s-7-4.4-9-8.5C1.6 8.3 3.3 5.5 6.3 5.5c1.9 0 3 1.1 3.7 2.2.7-1.1 1.8-2.2 3.7-2.2 3 0 4.7 2.8 3.3 6C19 15.6 12 20 12 20z" /></Svg>);
const IcHome = ({ className }: IconProps) => (<Svg className={className}><path d="M4 11l8-6 8 6M6 10v9h12v-9" /></Svg>);
const IcSparkle = ({ className }: IconProps) => (<svg className={className} viewBox="0 0 24 24" fill="currentColor" aria-hidden><path d="M12 3l1.6 5L19 9.6l-5 1.6L12 17l-1.6-5.8L5 9.6 10.4 8 12 3z" /></svg>);
const IcArrow = ({ className }: IconProps) => (<svg className={className} viewBox="0 0 40 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="M4 12h28M24 4l9 8-9 8" /></svg>);
const IcSun = ({ className }: IconProps) => (<Svg className={className}><circle cx="12" cy="12" r="4.2" /><path d="M12 2.5v2.4M12 19.1v2.4M4.6 4.6l1.7 1.7M17.7 17.7l1.7 1.7M2.5 12h2.4M19.1 12h2.4M4.6 19.4l1.7-1.7M17.7 6.3l1.7-1.7" /></Svg>);
const IcMoon = ({ className }: IconProps) => (<Svg className={className}><path d="M20 15A8 8 0 1 1 10 4a6.5 6.5 0 0 0 10 11z" /></Svg>);
const IcChevron = ({ className }: IconProps) => (<Svg className={className}><path d="M6 9l6 6 6-6" /></Svg>);
const IcShield = ({ className }: IconProps) => (<Svg className={className}><path d="M12 3l7 2.5V11c0 4.4-3 7.7-7 9-4-1.3-7-4.6-7-9V5.5L12 3z" /><path d="M9.2 12l2 2 3.6-3.8" /></Svg>);
const IcEye = ({ className }: IconProps) => (<Svg className={className}><path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z" /><circle cx="12" cy="12" r="2.6" /></Svg>);
const IcTruck = ({ className }: IconProps) => (<Svg className={className}><path d="M3 6.5h11v9H3zM14 9.5h4l3 3v3h-7z" /><circle cx="7" cy="18" r="1.6" /><circle cx="17.5" cy="18" r="1.6" /></Svg>);
const IcPlay = ({ className }: IconProps) => (<Svg className={className}><rect x="3" y="5.5" width="18" height="13" rx="2.5" /><path d="M10 9.5l4.5 2.5-4.5 2.5z" fill="currentColor" stroke="none" /></Svg>);
const IcCheck = ({ className }: IconProps) => (<svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="M4 12.5l5 5L20 6.5" /></svg>);
const IcClose = ({ className }: IconProps) => (<svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="M6 6l12 12M18 6L6 18" /></svg>);

const NAV_ICONS = [IcHome, IcBook, IcSparkle, IcPlay];
const PROMISE_ICONS = [IcShield, IcGift, IcEye, IcTruck];

/* ------- exemplos reais em apps/web/public/exemplos/ ------- */
const HOW_IMGS = ["foto-matteo.png", "personagem-dino.jpg", "capa-dino2.jpg"];
// Dicas de enquadramento: 1 exemplo bom (verde) + 2 a evitar (X).
// img = foto real local (public/exemplos/) ou URL externa; art = ilustração SVG de fallback.
const SHOTS: { img?: string; art?: "good" | "multi" | "side" | "covered"; ok: boolean; focus?: string }[] = [
  { img: "dica-boa.png", ok: true, focus: "center center" },
  { img: "dica-multi.png", ok: false, focus: "center center" },
  { img: "dica-lado.png", ok: false, focus: "center center" },
];
const BOOK = Array.from({ length: 11 }, (_, i) => `ebook-${i + 1}.jpg`);
const CATALOG_IMGS = ["capa-oceano.jpg", "capa-floresta2.jpg", "capa-dino2.jpg", "capa-circo.jpg"];
const CATALOG_THEMES = ["underwater", "fantasy", "dinosaurs", "adventure"];
const SURPRISE_IMG = "capa-surpresa.jpg";
/* livro 3D do catálogo: 6 páginas internas (3 spreads) do livro de exemplo de cada tema */
const BOOK3D = [
  { bg: "#cfe3f0", pages: ["mar-1.jpg", "mar-2.jpg", "mar-3.jpg", "mar-4.jpg", "mar-5.jpg", "mar-6.jpg"] },
  { bg: "#e2e6d1", pages: ["flor-1.jpg", "flor-2.jpg", "flor-3.jpg", "flor-4.jpg", "flor-5.jpg", "flor-6.jpg"] },
  { bg: "#ecd8b2", pages: ["dino-1.jpg", "dino-2.jpg", "dino-3.jpg", "dino-4.jpg", "dino-5.jpg", "dino-6.jpg"] },
  { bg: "#f4d6da", pages: ["circo-1.jpg", "circo-2.jpg", "circo-3.jpg", "circo-4.jpg", "circo-5.jpg", "circo-6.jpg"] },
];
const BOOK3D_SURPRISE = { bg: "#f3e2b4", pages: ["ebook-6.jpg", "ebook-9.jpg", "ebook-8.jpg", "ebook-10.jpg", "ebook-7.jpg", "ebook-4.jpg"] };
const BANNER_IMGS = ["capa-circo.jpg", "capa-oceano.jpg", "capa-dino2.jpg"];
const VIDEO_IMGS = ["mar-2.jpg", "flor-2.jpg", "circo-2.jpg"];
// Slides do hero: foto real (em cima) -> capa do livro gerado
const HERO_SLIDES: { photo: string; book: string; photoPos?: string }[] = [
  { photo: "foto-matteo.png", book: "capa-circo.jpg", photoPos: "center 22%" },
  { photo: "foto-sofia.png", book: "capa-floresta.jpg" },
  { photo: "foto-bebe.jpg", book: "capa-oceano.jpg" },
];
const exUrl = (f: string) => (f.startsWith("http://") || f.startsWith("https://") ? f : `${import.meta.env.BASE_URL}exemplos/${f}`);

/* Ilustrações das dicas de enquadramento (SVG inline, sem depender de fotos) */
function ShotArt({ kind }: { kind: "good" | "multi" | "side" | "covered" }) {
  const face = "#f4c19a", hair = "#6b4a2b", eye = "#3a2b1c", mouth = "#a15a3a";
  if (kind === "multi") {
    return (
      <svg className="shot-svg" viewBox="0 0 120 120" preserveAspectRatio="xMidYMid slice" aria-hidden>
        <rect width="120" height="120" fill="#e7ecf4" />
        <g>
          <rect x="24" y="76" width="20" height="26" rx="10" fill="#8fb4dd" />
          <circle cx="34" cy="58" r="16" fill={face} /><path d="M19 57q0-18 15-18t15 18q0-9-15-9t-15 9Z" fill="#7a5230" />
          <circle cx="29" cy="57" r="2.1" fill={eye} /><circle cx="39" cy="57" r="2.1" fill={eye} /><path d="M29 63q5 4 10 0" stroke={mouth} strokeWidth="2" fill="none" strokeLinecap="round" />
        </g>
        <g>
          <rect x="76" y="76" width="20" height="26" rx="10" fill="#8ccdb0" />
          <circle cx="86" cy="58" r="16" fill={face} /><path d="M71 57q0-18 15-18t15 18q0-9-15-9t-15 9Z" fill={hair} />
          <circle cx="81" cy="57" r="2.1" fill={eye} /><circle cx="91" cy="57" r="2.1" fill={eye} /><path d="M81 63q5 4 10 0" stroke={mouth} strokeWidth="2" fill="none" strokeLinecap="round" />
        </g>
        <g>
          <rect x="47" y="72" width="26" height="34" rx="12" fill="#e79a9a" />
          <circle cx="60" cy="52" r="19" fill="#eab98f" /><path d="M41 51q0-21 19-21t19 21q0-10-19-10t-19 10Z" fill="#4a3320" />
          <circle cx="54" cy="51" r="2.4" fill={eye} /><circle cx="66" cy="51" r="2.4" fill={eye} /><path d="M54 58q6 5 12 0" stroke={mouth} strokeWidth="2.2" fill="none" strokeLinecap="round" />
        </g>
      </svg>
    );
  }
  if (kind === "side") {
    return (
      <svg className="shot-svg" viewBox="0 0 120 120" preserveAspectRatio="xMidYMid slice" aria-hidden>
        <rect width="120" height="120" fill="#e7ecf4" />
        <rect x="50" y="88" width="16" height="18" rx="8" fill="#eeb086" />
        <circle cx="56" cy="60" r="28" fill={face} />
        <path d="M28 60q0-30 28-30 16 0 25 12l-12 3q-7-9-17-7-24 4-24 22Z" fill={hair} />
        <path d="M30 62q-3 14 10 20-8-16-2-28-5 2-8 8Z" fill={hair} />
        <circle cx="46" cy="63" r="4" fill="#eeb086" />
        <path d="M83 57q7 4 0 9" fill={face} stroke="#e2a880" strokeWidth="1.4" />
        <circle cx="71" cy="58" r="3.1" fill={eye} />
        <path d="M70 72q7 3 12 0" stroke={mouth} strokeWidth="2.6" fill="none" strokeLinecap="round" />
      </svg>
    );
  }
  if (kind === "covered") {
    return (
      <svg className="shot-svg" viewBox="0 0 120 120" preserveAspectRatio="xMidYMid slice" aria-hidden>
        <rect width="120" height="120" fill="#e7ecf4" />
        <rect x="52" y="88" width="16" height="18" rx="8" fill="#eeb086" />
        <circle cx="60" cy="60" r="30" fill={face} />
        <path d="M30 58q0-30 30-30t30 30q0-14-12-18-8-8-18-8t-18 8q-12 4-12 18Z" fill={hair} />
        <circle cx="50" cy="56" r="3.3" fill={eye} /><circle cx="70" cy="56" r="3.3" fill={eye} />
        <path d="M34 66q26-6 52 0l0 8q-26 18-52 0Z" fill="#7f9bc4" />
        <path d="M34 66l-6 4M86 66l6 4" stroke="#7f9bc4" strokeWidth="3" strokeLinecap="round" />
      </svg>
    );
  }
  return (
    <svg className="shot-svg" viewBox="0 0 120 120" preserveAspectRatio="xMidYMid slice" aria-hidden>
      <rect width="120" height="120" fill="#ffe0b0" />
      <circle cx="97" cy="23" r="15" fill="#fff2cf" opacity="0.85" />
      <rect x="52" y="86" width="16" height="18" rx="8" fill="#eeb086" />
      <circle cx="60" cy="62" r="30" fill={face} />
      <path d="M30 60q0-32 30-32t30 32q0-14-12-18-8-8-18-8t-18 8q-12 4-12 18Z" fill={hair} />
      <circle cx="50" cy="60" r="3.4" fill={eye} /><circle cx="70" cy="60" r="3.4" fill={eye} />
      <circle cx="46" cy="70" r="4" fill="#f2a982" opacity=".6" /><circle cx="74" cy="70" r="4" fill="#f2a982" opacity=".6" />
      <path d="M49 74q11 10 22 0" stroke={mouth} strokeWidth="3" fill="none" strokeLinecap="round" />
    </svg>
  );
}

function Faq({ items }: { items: readonly { q: string; a: string }[] }) {
  const [open, setOpen] = useState<number | null>(0);
  return (
    <div className="faq">
      {items.map((it, i) => (
        <div className={`faq-item${open === i ? " open" : ""}`} key={it.q}>
          <button className="faq-q" onClick={() => setOpen(open === i ? null : i)} aria-expanded={open === i}>
            <span>{it.q}</span><IcChevron className="faq-chev" />
          </button>
          <div className="faq-a"><p>{it.a}</p></div>
        </div>
      ))}
    </div>
  );
}

function FlipBook({ pages, compact = false }: { pages: string[]; compact?: boolean }) {
  const [i, setI] = useState(0);
  const [anim, setAnim] = useState<"next" | "prev" | null>(null);
  const [target, setTarget] = useState(0);
  const [hover, setHover] = useState(false);
  const busy = useRef(false);
  const flip = (dir: "next" | "prev", loop = false) => {
    if (busy.current) return;
    let t = dir === "next" ? i + 1 : i - 1;
    if (t >= pages.length) { if (!loop) return; t = 0; }
    if (t < 0) return;
    busy.current = true;
    setTarget(t);
    setAnim(dir);
    window.setTimeout(() => { setI(t); setAnim(null); busy.current = false; }, 720);
  };
  // transição automática — vira a página sozinho; no modo compacto (catálogo) só roda com o mouse em cima
  useEffect(() => {
    if (compact && !hover) return;
    const id = window.setTimeout(() => flip("next", true), 1500);
    return () => window.clearTimeout(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [i, pages.length, compact, hover]);
  // ao tirar o mouse no modo compacto, volta parado na capa
  useEffect(() => {
    if (compact && !hover) {
      busy.current = false;
      setAnim(null);
      setI(0);
    }
  }, [hover, compact]);
  const baseSrc = anim === "next" ? pages[target] : pages[i];
  const turnSrc = anim === "next" ? pages[i] : pages[target];
  const onStage = (e: RMouseEvent<HTMLDivElement>) => {
    const r = e.currentTarget.getBoundingClientRect();
    if (e.clientX - r.left > r.width / 2) flip("next", true); else flip("prev");
  };
  return (
    <div
      className={`flipbook${compact ? " flipbook-mini" : ""}`}
      onMouseEnter={compact ? () => setHover(true) : undefined}
      onMouseLeave={compact ? () => setHover(false) : undefined}
    >
      {!compact && <button className="fb-nav" onClick={() => flip("prev")} disabled={i === 0} aria-label="Página anterior">‹</button>}
      <div className="fb-stage" onClick={onStage} role="button" tabIndex={0} aria-label="Virar página">
        <span className="fb-spine" />
        <img className="fb-page fb-base" src={exUrl(baseSrc)} alt={`Página ${i + 1}`} />
        {anim && <img className={`fb-page fb-turn ${anim}`} src={exUrl(turnSrc)} alt="" aria-hidden />}
        <span className="fb-count">{i + 1} / {pages.length}</span>
      </div>
      {!compact && <button className="fb-nav" onClick={() => flip("next")} disabled={i === pages.length - 1} aria-label="Próxima página">›</button>}
    </div>
  );
}

const I18N = {
  pt: {
    nav: ["Início", "Livros", "Como funciona", "Vídeos"],
    explore: "Explorar agora",
    eyebrow: "Sua foto vira uma história",
    h_pre: "Transforme uma foto em uma ", w1: "história", c1: " onde seu filho é o ", w2: "herói", h_suf: ".",
    lead: "Você envia a foto e a gente cria um personagem ilustrado, uma história personalizada, um livro em PDF e até um vídeo narrado.",
    cta_play: "Criar minha história", cta_disc: "Ver como funciona",
    trust: "Encantando famílias do início ao fim",
    ba_before: "ANTES", ba_after: "DEPOIS", ba_caption: "Você envia a foto. A gente cria o encanto.",
    ba_preview: "PRÉ-VISUALIZAÇÃO",
    ba_title: "Antes e depois de verdade",
    ba_sub: "Fotos reais transformadas em personagens ilustrados.",
    ba_pairs: ["Do berço para a aventura", "Uma menina cheia de imaginação", "Sorriso que vira personagem", "Da foto ao herói da história", "Todo mundo pode ser protagonista"],
    banners: [
      { t: "Voe com a imaginação", p: "Cada página abre uma aventura nova onde seu filho é o protagonista." },
      { t: "Construa a própria história", p: "Escolha a aventura, personalize os detalhes e crie um livro único." },
      { t: "Explore mundos incríveis", p: "Aventuras que despertam a curiosidade e alimentam a imaginação." },
    ],
    hiw_title: "Como funciona", hiw_sub: "Da sua foto ao livro — com exemplos reais.",
    hiw: [
      { t: "Você envia a foto", p: "Uma foto da criança já basta para começar." },
      { t: "Criamos o personagem e a história", p: "Ilustração fiel à foto e um texto só de vocês." },
      { t: "Sua família vira o livro", p: "Páginas ilustradas, para guardar para sempre." },
    ],
    shot_title: "Dicas para a foto perfeita",
    shot_sub: "Envie uma foto nítida da criança, com o rosto centralizado. Os exemplos com X mostram o que evitar.",
    shots: ["Nítida, bem iluminada e centralizada", "Mais de uma pessoa na foto", "Rosto de lado"],
    vid_title: "Vídeos narrados", vid_sub: "A mesma história ganha voz, trilha e movimento — perfeita para assistir em família.",
    vid_dur: "~2 min", vid_cta: "Criar meu vídeo",
    videos: [
      { t: "Fundo do Mar", p: "Uma aventura no oceano com narração encantadora." },
      { t: "Floresta Encantada", p: "Bichinhos gentis e luzes de vaga-lume, com trilha suave." },
      { t: "Circo das Luzes", p: "Uma noite mágica cheia de brilho e música." },
    ],
    book_badge: "Exemplo real",
    story_title: "Folheie um livro de verdade",
    story_sub: "Livros criados pela plataforma a partir de uma única foto — escolha um exemplo.",
    story_hint: "Clique nas laterais do livro (ou use as setas) para virar as páginas.",
    chloe_title: "A História de Chloe",
    fmt_title: "Escolha o formato", fmt_sub: "Do mesmo personagem, três formas de guardar a história.",
    formats: [
      { t: "Livro para impressão", price: "US$ 39,99", unit: "por livro", p: "Um livro ilustrado em PDF, pronto para imprimir e ter na estante.", feats: ["Capa + páginas ilustradas", "PDF em alta para impressão", "Personagem fiel à foto"], cta: "Criar meu livro", badge: "Mais amado" },
      { t: "Vídeo narrado", price: "R$ 89", unit: "por vídeo", p: "A história ganha voz e trilha, perfeita para assistir em família.", feats: ["Narração encantadora", "Cenas ilustradas", "Fácil de compartilhar"], cta: "Criar meu vídeo", badge: "" },
      { t: "Animação", price: "R$ 149", unit: "por animação", p: "O personagem ganha vida numa animação cheia de magia.", feats: ["Movimento e magia", "Baseada na sua história", "Um presente diferente"], cta: "Criar animação", badge: "" },
    ],
    cat_title: "Escolha um livro", cat_sub: "Cada tema vira uma história ilustrada com seu filho como protagonista.",
    price: "US$ 39,99", price_note: "digital ou impresso", personalize: "Personalizar",
    save: "ECONOMIZE 33%",
    catalog: [
      { t: "Fundo do Mar", p: "Uma aventura no oceano com amigos marinhos.", age: "3-6 anos", tag: "Coragem e amizade", quote: "Coragem que mergulha fundo — e volta com amigos." },
      { t: "Floresta Encantada", p: "Bichinhos gentis e luzes mágicas de vaga-lume.", age: "3-6 anos", tag: "Gentileza e natureza", quote: "Onde a gentileza acende vaga-lumes." },
      { t: "Mundo dos Dinossauros", p: "Um vale cheio de dinossauros dóceis.", age: "4-7 anos", tag: "Descoberta e curiosidade", quote: "Uma viagem divertida à era dos dinossauros." },
      { t: "Circo das Luzes", p: "Uma noite mágica cheia de brilho.", age: "3-6 anos", tag: "Sonhar e brilhar", quote: "Uma noite feita para sonhar e brilhar." },
    ],
    surprise: { t: "História Surpresa (IA)", p: "Deixe a IA inventar uma aventura única a partir da foto.", age: "3-8 anos", tag: "Aventura sob medida", quote: "Cada foto guarda uma aventura secreta." },
    promise_title: "Cada detalhe pensado para ser especial",
    promise_sub: "Do envio da foto à entrega, tudo é feito para o livro chegar pronto para presentear.",
    promise: [
      { t: "Privacidade da foto", p: "A imagem é usada só para preparar o livro do seu filho — nunca para divulgação." },
      { t: "Impressão pensada como presente", p: "Preparado para ficar lindo em mãos, na leitura em família e na hora de entregar." },
      { t: "Prévia antes de avançar", p: "Você vê a capa e as páginas e entende o que está criando antes de finalizar." },
      { t: "Entrega sem complicação", p: "Acompanhamos da personalização ao envio para tudo chegar prontinho." },
    ],
    faq_title: "Perguntas frequentes", faq_sub: "Tudo o que você precisa saber.",
    faq: [
      { q: "Como crio um livro personalizado?", a: "Escolha um tema, envie uma foto da criança e adicione o nome e uma dedicatória. A IA transforma a foto em ilustrações e você vê a prévia antes de finalizar." },
      { q: "Posso ver o livro antes?", a: "Sim! Você recebe uma prévia completa (capa e páginas) antes de baixar ou pedir a impressão." },
      { q: "A foto e os dados da criança estão seguros?", a: "Sim. Usamos a foto apenas para criar o livro e não compartilhamos seus dados." },
      { q: "Recebo digital ou impresso?", a: "Os dois: o e-book digital na hora e, se quiser, o livro impresso enviado até você." },
      { q: "Posso pedir alterações?", a: "Pode! Ajuste o nome, a dedicatória e regenere as ilustrações na prévia até ficar do seu jeito." },
    ],
    rev_title: "O que as famílias dizem", rev_sub: "Histórias que viraram memórias para sempre.",
    reviews: [
      { q: "Meu filho pede para ler o livro dele toda noite. Emocionante vê-lo como herói!", name: "Ana C." },
      { q: "Enviei uma foto e recebi um livro lindo. Virou o presente de aniversário da vovó.", name: "Rafael M." },
      { q: "A ilustração ficou idêntica ao meu bebê. Vamos guardar para sempre.", name: "Juliana P." },
      { q: "O vídeo narrado fez a família toda se emocionar. Vale cada segundo.", name: "Marcos e Bia" },
    ],
    features: ["Histórias personalizadas", "Conexão em família", "Memórias que ficam para sempre", "Um presente inesquecível"],
    band_title: "Pronto para virar protagonista?",
    band_sub: "Envie sua foto e receba uma história única, criada só para você.",
    band_cta: "Criar minha história",
    tagline: "Feito com amor. Criado para encantar.",
    foot_copy: "© 2026 Story R Us — Where Memories Become Magic.",
  },
  en: {
    nav: ["Home", "Books", "How it works", "Videos"],
    explore: "Explore now",
    eyebrow: "Your photo becomes a story",
    h_pre: "Turn a photo into a ", w1: "story", c1: " where your child is the ", w2: "hero", h_suf: ".",
    lead: "You send the photo and we create an illustrated character, a personalized story, a PDF book and even a narrated video.",
    cta_play: "Create my story", cta_disc: "See how it works",
    trust: "Delighting families from start to finish",
    ba_before: "BEFORE", ba_after: "AFTER", ba_caption: "You send the photo. We create the magic.",
    ba_preview: "PREVIEW",
    ba_title: "Real before and after",
    ba_sub: "Real photos turned into illustrated characters.",
    ba_pairs: ["From crib to adventure", "A girl full of imagination", "A smile that becomes a character", "From photo to story hero", "Anyone can be the hero"],
    banners: [
      { t: "Fly with imagination", p: "Every page opens a new adventure where your child is the hero." },
      { t: "Build their own story", p: "Choose the adventure, personalize the details and create a unique book." },
      { t: "Explore amazing worlds", p: "Adventures that spark curiosity and feed the imagination." },
    ],
    hiw_title: "How it works", hiw_sub: "From your photo to the book — with real examples.",
    hiw: [
      { t: "You send the photo", p: "One photo of your child is all it takes to begin." },
      { t: "We create the character and story", p: "An illustration true to the photo and a story that's all yours." },
      { t: "Your family becomes the book", p: "Illustrated pages, made to keep forever." },
    ],
    shot_title: "Tips for the perfect photo",
    shot_sub: "Upload a clear photo of your child with the face centered. The X examples show what to avoid.",
    shots: ["Clear, well-lit and centered", "More than one person in the photo", "Face at an angle"],
    vid_title: "Narrated videos", vid_sub: "The same story gains voice, music and motion — perfect to watch together.",
    vid_dur: "~2 min", vid_cta: "Create my video",
    videos: [
      { t: "Underwater World", p: "An ocean adventure with enchanting narration." },
      { t: "Enchanted Forest", p: "Gentle little creatures and firefly lights, with a soft soundtrack." },
      { t: "Circus of Lights", p: "A magical night full of sparkle and music." },
    ],
    book_badge: "Real example",
    story_title: "Flip through a real book",
    story_sub: "Books created by the platform from a single photo — pick an example.",
    story_hint: "Click the sides of the book (or use the arrows) to turn the pages.",
    chloe_title: "Chloe's Story",
    fmt_title: "Choose the format", fmt_sub: "From the same character, three ways to keep the story.",
    formats: [
      { t: "Printable book", price: "$39.99", unit: "per book", p: "An illustrated PDF book, ready to print and keep on the shelf.", feats: ["Cover + illustrated pages", "High-res PDF for printing", "Character true to the photo"], cta: "Create my book", badge: "Most loved" },
      { t: "Narrated video", price: "$49", unit: "per video", p: "The story gets a voice and music, perfect to watch together.", feats: ["Enchanting narration", "Illustrated scenes", "Easy to share"], cta: "Create my video", badge: "" },
      { t: "Animation", price: "$79", unit: "per animation", p: "The character comes alive in a magical animation.", feats: ["Movement and magic", "Based on your story", "A different gift"], cta: "Create animation", badge: "" },
    ],
    cat_title: "Choose a book", cat_sub: "Each theme becomes an illustrated story with your child as the hero.",
    price: "$39.99", price_note: "digital or printed", personalize: "Personalize",
    save: "SAVE 33%",
    catalog: [
      { t: "Deep Sea", p: "An ocean adventure with sea friends.", age: "ages 3-6", tag: "Courage & friendship", quote: "Courage that dives deep — and comes back with friends." },
      { t: "Enchanted Forest", p: "Gentle creatures and magical firefly lights.", age: "ages 3-6", tag: "Kindness & nature", quote: "Where kindness lights up the fireflies." },
      { t: "Dinosaur World", p: "A valley full of gentle dinosaurs.", age: "ages 4-7", tag: "Discovery & curiosity", quote: "A fun journey back to the dinosaur age." },
      { t: "Circus of Lights", p: "A magical night full of sparkle.", age: "ages 3-6", tag: "Dream & shine", quote: "A night made to dream and shine." },
    ],
    surprise: { t: "Surprise Story (AI)", p: "Let the AI invent a unique adventure from the photo.", age: "ages 3-8", tag: "Made-to-fit adventure", quote: "Every photo hides a secret adventure." },
    promise_title: "Every detail crafted to feel special",
    promise_sub: "From the photo to delivery, everything is made so the book arrives ready to gift.",
    promise: [
      { t: "Photo privacy", p: "The image is used only to prepare your child's book — never for promotion." },
      { t: "Print made as a gift", p: "Prepared to look beautiful in hand, in shared reading and at the moment you give it." },
      { t: "Preview before you continue", p: "You see the cover and pages and understand what you're creating before finishing." },
      { t: "Hassle-free delivery", p: "We follow from personalization to shipping so everything arrives ready." },
    ],
    faq_title: "Frequently asked questions", faq_sub: "Everything you need to know.",
    faq: [
      { q: "How do I create a personalized book?", a: "Pick a theme, upload a photo of your child and add the name and a dedication. The AI turns the photo into illustrations and you see a preview before finishing." },
      { q: "Can I see the book before?", a: "Yes! You get a full preview (cover and pages) before downloading or ordering the print." },
      { q: "Are my child's photo and data safe?", a: "Yes. We use the photo only to create the book and never share your data." },
      { q: "Digital or printed?", a: "Both: the digital e-book right away and, if you want, the printed book shipped to you." },
      { q: "Can I request changes?", a: "You can! Adjust the name, the dedication and regenerate the illustrations in the preview." },
    ],
    rev_title: "What families say", rev_sub: "Stories that became memories forever.",
    reviews: [
      { q: "My son asks to read his book every night. Seeing him as the hero is moving!", name: "Ana C." },
      { q: "I sent a photo and got a beautiful book. It became grandma's birthday gift.", name: "Rafael M." },
      { q: "The illustration looks just like my baby. We'll keep it forever.", name: "Juliana P." },
      { q: "The narrated video moved the whole family. Worth every second.", name: "Marcos & Bia" },
    ],
    features: ["Personalized stories", "Family connection", "Memories that last forever", "An unforgettable gift"],
    band_title: "Ready to become the hero?",
    band_sub: "Send your photo and get a unique story, made just for you.",
    band_cta: "Create my story",
    tagline: "Made with love. Created to enchant.",
    foot_copy: "© 2026 Story R Us — Where Memories Become Magic.",
  },
} as const;

export function Landing() {
  const rootRef = useRef<HTMLDivElement>(null);
  const [navOpen, setNavOpen] = useState(false);
  const [lang, setLang] = useState<Lang>("pt");
  const [theme, setTheme] = useState<"light" | "dark">(() => {
    try { const s = localStorage.getItem("theme"); if (s === "light" || s === "dark") return s; } catch { /* ignore */ }
    return "dark";
  });
  const [heroI, setHeroI] = useState(0);
  const [exBook, setExBook] = useState(0);
  const t = I18N[lang];
  const navHrefs = ["#top", "#catalogo", "#como", "#videos"];
  const exampleBooks = [
    { title: t.catalog[0].t, cover: CATALOG_IMGS[0], pages: [CATALOG_IMGS[0], ...BOOK3D[0].pages] },
    { title: t.chloe_title, cover: "ebook-1.jpg", pages: BOOK },
    ...t.catalog.slice(1).map((c, i) => ({ title: c.t, cover: CATALOG_IMGS[i + 1], pages: [CATALOG_IMGS[i + 1], ...BOOK3D[i + 1].pages] })),
  ];

  // Auto-avanço do carrossel do hero
  useEffect(() => {
    const id = setInterval(() => setHeroI((v) => (v + 1) % HERO_SLIDES.length), 5200);
    return () => clearInterval(id);
  }, []);
  const featIcons = [IcSparkle, IcHeart, IcBook, IcGift];

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    try { localStorage.setItem("theme", theme); } catch { /* ignore */ }
  }, [theme]);

  useEffect(() => {
    const els = rootRef.current?.querySelectorAll(".reveal") ?? [];
    const io = new IntersectionObserver((entries) => {
      entries.forEach((en) => { if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); } });
    }, { threshold: 0.12 });
    els.forEach((el, i) => { (el as HTMLElement).style.transitionDelay = `${(i % 3) * 0.1}s`; io.observe(el); });
    return () => io.disconnect();
  }, []);

  const closeNav = () => setNavOpen(false);

  return (
    <div className="kid" ref={rootRef} id="top">
      <div className="sky" aria-hidden>
        <IcStar className="dstar d1" /><IcStar className="dstar d2" /><IcSparkle className="dstar d3" /><IcStar className="dstar d4" />
        <svg className="dmoon m1" viewBox="0 0 24 24" aria-hidden><path d="M17 15A8 8 0 1 1 9 4a7 7 0 0 0 8 11z" fill="#f4b740" /></svg>
        <svg className="dmoon m2" viewBox="0 0 24 24" aria-hidden><path d="M17 15A8 8 0 1 1 9 4a7 7 0 0 0 8 11z" fill="#7fb2e3" /></svg>
      </div>

      <header className="knav">
        <a href="#top" className="kbrand"><img src={logo} alt="Story.R.Us" /></a>
        <nav className={`klinks${navOpen ? " open" : ""}`}>
          {t.nav.map((label, i) => {
            const Icon = NAV_ICONS[i];
            return (<a key={label} href={navHrefs[i]} onClick={closeNav}><Icon className="ni" />{label}</a>);
          })}
          <Link to="/app" className="kbtn kbtn-go" onClick={closeNav}>{t.cta_play}</Link>
        </nav>
        <div className="kright">
          <button className="theme-toggle" onClick={() => setTheme(theme === "dark" ? "light" : "dark")} aria-label="Alternar tema claro/escuro">
            {theme === "dark" ? <IcSun className="ti" /> : <IcMoon className="ti" />}
          </button>
          <div className="lang" role="group" aria-label="Idioma / Language">
            <button className={lang === "pt" ? "on" : ""} onClick={() => setLang("pt")}>PT</button>
            <button className={lang === "en" ? "on" : ""} onClick={() => setLang("en")}>EN</button>
          </div>
          <button className="khamb" aria-label="Menu" onClick={() => setNavOpen((v) => !v)}>☰</button>
        </div>
      </header>

      {/* HERO — banner full-width (foto real em cima -> capa do livro), carrossel */}
      <section className="kbanner-hero" aria-label={t.eyebrow}>
        <div className="kbh-frame">
          {HERO_SLIDES.map((s, i) => (
            <div className={`kbh-slide${i === heroI ? " on" : ""}`} key={s.book} aria-hidden={i !== heroI}>
              <img
                className="kbh-photo"
                src={exUrl(s.book)}
                alt="Capa do livro gerado"
                loading={i === 0 ? "eager" : "lazy"}
              />
              <span className="kbh-tag">
                <span className="kbh-tag-top"><IcEye className="ei" /> {t.ba_preview}</span>
                <b>{t.banners[i].t}</b>
              </span>
              <figure className="kbh-book">
                <img
                  src={exUrl(s.photo)}
                  alt="Foto real da criança"
                  loading={i === 0 ? "eager" : "lazy"}
                  style={s.photoPos ? { objectPosition: s.photoPos } : undefined}
                />
              </figure>
              <div className="kbh-overlay">
                <span className="keyebrow"><IcSparkle className="ei" /> {t.eyebrow}</span>
                <h1>{t.banners[i].t}.</h1>
                <p>{t.banners[i].p}</p>
                <div className="khero-cta">
                  <Link to="/app" className="kbtn kbtn-primary">{t.cta_play}</Link>
                </div>
              </div>
            </div>
          ))}
          <div className="ba-dots kbh-dots">
            {HERO_SLIDES.map((_, i) => (
              <button
                key={i}
                className={i === heroI ? "on" : ""}
                onClick={() => setHeroI(i)}
                aria-label={`Slide ${i + 1}`}
                aria-current={i === heroI}
              />
            ))}
          </div>
        </div>
      </section>

      {/* FLIPBOOK — destaque */}
      <section className="ksection featured-book" id="historia-exemplo">
        <span className="book-badge reveal"><IcStar className="bi" /> {t.book_badge}</span>
        <h2 className="ktitle reveal">{t.story_title}</h2>
        <p className="ksub reveal">{t.story_sub}</p>
        <div className="ex-tabs reveal" role="tablist" aria-label={t.story_title}>
          {exampleBooks.map((b, i) => (
            <button
              key={b.title}
              type="button"
              className={`ex-tab${i === exBook ? " on" : ""}`}
              onClick={() => setExBook(i)}
              role="tab"
              aria-selected={i === exBook}
            >
              <img src={exUrl(b.cover)} alt={b.title} loading="lazy" />
              <span>{b.title}</span>
            </button>
          ))}
        </div>
        <div className="reveal"><FlipBook key={exBook} pages={exampleBooks[exBook].pages} /></div>
        <p className="fb-hint reveal">{t.story_hint}</p>
      </section>

      {/* BANNERS NARRATIVOS */}
      <section className="banners">
        {t.banners.map((b, i) => (
          <figure className="banner-card reveal" key={b.t}>
            <img src={exUrl(BANNER_IMGS[i])} alt={b.t} loading="lazy" />
            <figcaption><h3>{b.t}</h3><p>{b.p}</p></figcaption>
          </figure>
        ))}
      </section>

      {/* CATÁLOGO DE LIVROS */}
      <section className="ksection" id="catalogo">
        <h2 className="ktitle reveal">{t.cat_title}</h2>
        <p className="ksub reveal">{t.cat_sub}</p>
        <div className="cat-grid">
          {t.catalog.map((c, i) => (
            <div className="cat-card reveal" key={c.t}>
              <div className="cat-flip" style={{ background: BOOK3D[i].bg }}>
                <FlipBook pages={[CATALOG_IMGS[i], ...BOOK3D[i].pages]} compact />
                <span className="cat-flip-off">{t.save}</span>
              </div>
              <div className="cat-body">
                <div className="cat-badges"><span className="cat-age">{c.age}</span><span className="cat-tag">{c.tag}</span></div>
                <h3>{c.t}</h3>
                <p>{c.p}</p>
                <div className="cat-price">{t.price}<span>· {t.price_note}</span></div>
                <Link to={`/app?tema=${CATALOG_THEMES[i]}`} className="kbtn kbtn-primary">{t.personalize}</Link>
              </div>
            </div>
          ))}
          <div className="cat-card surprise reveal">
            <div className="cat-flip" style={{ background: BOOK3D_SURPRISE.bg }}>
              <FlipBook pages={[SURPRISE_IMG, ...BOOK3D_SURPRISE.pages]} compact />
            </div>
            <div className="cat-body">
              <div className="cat-badges"><span className="cat-age">{t.surprise.age}</span><span className="cat-tag">{t.surprise.tag}</span></div>
              <h3>{t.surprise.t}</h3>
              <p>{t.surprise.p}</p>
              <div className="cat-price">{t.price}<span>· {t.price_note}</span></div>
              <Link to="/app" className="kbtn kbtn-soft">{t.personalize}</Link>
            </div>
          </div>
        </div>
      </section>

      {/* COMO FUNCIONA — com exemplos reais */}
      <section className="ksection" id="como">
        <h2 className="ktitle reveal">{t.hiw_title}</h2>
        <p className="ksub reveal">{t.hiw_sub}</p>
        <div className="howex">
          {t.hiw.map((h, i) => (
            <div className="howex-item" key={h.t}>
              <figure className="howex-card reveal">
                <img src={exUrl(HOW_IMGS[i])} alt={h.t} loading="lazy" />
                <span className="howex-num">{i + 1}</span>
                <figcaption><h3>{h.t}</h3><p>{h.p}</p></figcaption>
              </figure>
              {i < t.hiw.length - 1 && <span className="howex-arrow" aria-hidden><IcArrow /></span>}
            </div>
          ))}
        </div>

        <div className="shot-tips reveal">
          <h3>{t.shot_title}</h3>
          <p className="shot-sub">{t.shot_sub}</p>
          <div className="shot-grid">
            {SHOTS.map((s, i) => (
              <div className={`shot${s.ok ? " ok" : ""}`} key={i}>
                <div className="shot-ava-wrap">
                  <div className="shot-ava">
                    {s.img ? (
                      <img src={exUrl(s.img)} alt={t.shots[i]} loading="lazy" style={{ objectPosition: s.focus ?? "center center" }} />
                    ) : (
                      <ShotArt kind={s.art ?? "good"} />
                    )}
                  </div>
                  <span className="shot-badge">{s.ok ? <IcCheck /> : <IcClose />}</span>
                </div>
                <p>{t.shots[i]}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* VÍDEOS NARRADOS */}
      <section className="ksection" id="videos">
        <h2 className="ktitle reveal">{t.vid_title}</h2>
        <p className="ksub reveal">{t.vid_sub}</p>
        <div className="vid-grid">
          {t.videos.map((v, i) => (
            <figure className="vid-card reveal" key={v.t}>
              <div className="vid-thumb">
                <img src={exUrl(VIDEO_IMGS[i])} alt={v.t} loading="lazy" />
                <span className="vid-play" aria-hidden></span>
                <span className="vid-dur">{t.vid_dur}</span>
              </div>
              <figcaption><h3>{v.t}</h3><p>{v.p}</p></figcaption>
            </figure>
          ))}
        </div>
        <div className="vid-cta"><Link to="/app" className="kbtn kbtn-primary big">{t.vid_cta}</Link></div>
      </section>

      {/* AVALIAÇÕES */}
      <section className="ksection" id="reviews">
        <h2 className="ktitle reveal">{t.rev_title}</h2>
        <p className="ksub reveal">{t.rev_sub}</p>
        <div className="rev-grid">
          {t.reviews.map((r) => (
            <figure className="rev-card reveal" key={r.name}>
              <div className="rev-stars">★★★★★</div>
              <blockquote>{r.q}</blockquote>
              <figcaption><span className="rev-av">{r.name.charAt(0)}</span>{r.name}</figcaption>
            </figure>
          ))}
        </div>
      </section>

      {/* NOSSA PROMESSA */}
      <section className="ksection" id="promessa">
        <h2 className="ktitle reveal">{t.promise_title}</h2>
        <p className="ksub reveal">{t.promise_sub}</p>
        <div className="promise-grid">
          {t.promise.map((pr, i) => {
            const Icon = PROMISE_ICONS[i];
            return (
              <div className="promise-card reveal" key={pr.t}>
                <span className="promise-ic"><Icon /></span>
                <h3>{pr.t}</h3>
                <p>{pr.p}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* FAQ */}
      <section className="ksection" id="faq">
        <h2 className="ktitle reveal">{t.faq_title}</h2>
        <p className="ksub reveal">{t.faq_sub}</p>
        <div className="reveal"><Faq items={t.faq} /></div>
      </section>

      {/* FAIXA DE ATRIBUTOS */}
      <section className="featurebar" id="presente">
        {t.features.map((f, i) => {
          const Icon = featIcons[i];
          return (<div className="feat" key={f}><Icon className="feat-ic" /><span>{f}</span></div>);
        })}
      </section>

      {/* CTA */}
      <section className="kband" id="familias">
        <IcSparkle className="twk b1" /><IcStar className="twk b2" />
        <h2>{t.band_title}</h2><p>{t.band_sub}</p>
        <Link to="/app" className="kbtn kbtn-primary big">{t.band_cta}</Link>
      </section>

      {/* FOOTER */}
      <footer className="kfoot">
        <div className="kfoot-nav">
          {t.nav.map((label, i) => { const Icon = NAV_ICONS[i]; return (<a key={label} href={navHrefs[i]}><Icon className="ni" />{label}</a>); })}
        </div>
        <p className="kfoot-tag"><IcHeart className="ci" /> {t.tagline}</p>
        <p className="kfoot-copy">{t.foot_copy}</p>
      </footer>
    </div>
  );
}
