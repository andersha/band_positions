<script lang="ts">
  import type { BandType } from './types';

  interface Props {
    bandType?: BandType;
  }

  let { bandType = 'wind' }: Props = $props();
</script>

<div class="about-page">
  <section class="about-section">
    <h2>Om denne appen</h2>
    <p>
      Denne appen lar deg utforske historiske resultater fra NM {bandType === 'wind' ? 'janitsjar' : 'brass'}. 
      Du kan sammenligne korps, dirigenter og musikkstykker på tvers av år og divisjoner.
    </p>
  </section>

  <section class="about-section">
    <h3>Datakilder</h3>
    <ul>
      <li>
        <strong>Konkurransedata:</strong> Hentet fra <a href="https://nmjanitsjar.no" target="_blank" rel="noopener noreferrer">nmjanitsjar.no</a> 
        og <a href="https://nmbrass.no" target="_blank" rel="noopener noreferrer">nmbrass.no</a> sine rikholdige arkiver over NM-prestasjoner.
      </li>
      <li>
        <strong>Repertoardatabase:</strong> Bygget på bakgrunn av data fra <a href="https://windrep.org" target="_blank" rel="noopener noreferrer">windrep.org</a>, 
        som gir informasjon om komponister, vanskelighetsgrad og varighet for janitsjarmusikk.
      </li>
      <li>
        <strong>Musikkopptak:</strong> Lenker er knyttet fra NM-stykkene til utgivelsene av NM-musikk på 
        <strong>Spotify</strong> og <strong>Apple Music</strong> der dette er tilgjengelig.
      </li>
    </ul>
  </section>

  <section class="about-section">
    <h3>Funksjoner</h3>
    
    <h4>Sammenligning av korps</h4>
    <p>
      På korps-siden kan du sammenligne så mange korps du vil. Grafen viser hvordan den samlede plasseringen 
      utvikler seg år for år, på tvers av alle divisjoner korpset har deltatt i.
    </p>

    <h4>Sammenligning av dirigenter</h4>
    <p>
      Du kan også sammenligne dirigenter. Det du sammenligner da er det beste korpset til hver dirigent 
      i de årene dirigentene har vært aktive i NM. Dette gir deg et bilde av dirigentens beste prestasjoner 
      gjennom karrieren.
    </p>

    <h4>Musikkstykker og komponister</h4>
    <p>
      Du kan liste alle gangene et stykke har vært fremført i NM, samt se alle komponistene som har 
      vært brukt i NM-sammenheng. Dette gir deg oversikt over repertoaret og hvilke komponister 
      som er mest populære.
    </p>

    <h4>Resultatlister</h4>
    <p>
      På resultat-siden kan du velge et spesifikt år og en divisjon for å se den komplette resultatlisten 
      med korps, dirigenter, program og poengsum.
    </p>

    <h4>Sortering av tabeller</h4>
    <p>
      Alle tabeller kan sorteres ved å klikke på kolonneoverskriftene. Klikk én gang for å sortere, 
      og klikk igjen for å reversere sorteringsrekkefølgen. Tabeller sorteres som standard på år, 
      men du kan sortere på alle kolonner som år, divisjon, plass, poeng og dirigent/korps. 
      Divisjoner sorteres fra Elite til 1., 2., 3. divisjon osv.
    </p>

    <h4>Opprykk og nedrykk</h4>
    <p>
      I resultatlisten vises korps som rykker opp med <span class="indicator-promote">grønn bakgrunn</span> 
      og korps som rykker ned med <span class="indicator-demote">rød bakgrunn</span>. 
      De tre beste plassene i hver divisjon markeres med troféer: 🥇 gull, 🥈 sølv, og 🥉 bronse.
    </p>
    <p>
      Elitedivisjonen viser kun nedrykk (ingen opprykk mulig), mens den laveste divisjonen kun viser 
      opprykk (ingen nedrykk). For år uten definerte regler vises ingen fargemarkering.
    </p>
  </section>

  <section class="about-section">
    <h3>Navigasjon og innstillinger</h3>
    <ul>
      <li>
        <strong>Bytt mellom visninger:</strong> Bruk knappene øverst for å navigere mellom korps, dirigenter, 
        stykker, komponister, repertoar og resultatlister.
      </li>
      <li>
        <strong>Valg bevares:</strong> Appen husker alle valg du har gjort når du navigerer mellom sidene. 
        Når du bytter mellom janitsjar og brass, nullstilles alle valg.
      </li>
      <li>
        <strong>Tema:</strong> Du kan velge mellom lyst og mørkt modus ved å trykke på tema-knappen 
        (☀️/🌙) i menyen. Valget ditt lagres og gjenbrukes neste gang du besøker siden.
      </li>
      <li>
        <strong>Delbare lenker:</strong> URL-en oppdateres basert på dine valg, så du kan dele lenker 
        til spesifikke sammenligninger eller resultatlister med andre.
      </li>
    </ul>
  </section>

  <section class="about-section">
    <h3>Tips</h3>
    <ul>
      <li>På mobil kan du bruke hamburgermenyen (☰) for å få tilgang til alle navigasjonsalternativer.</li>
      <li>Klikk på korpsnavn, dirigenter eller stykker i tabellene for å legge dem til i sammenligningen.</li>
      <li>Bruk «Tilpass»-menyen på graf-siden for å bytte mellom absolutt og relativ plassering.</li>
      <li>Musikkopptak vises med Spotify- og Apple Music-ikoner der lenker er tilgjengelige.</li>
    </ul>
  </section>

  <section class="about-section about-footer">
    <p>
      Har du spørsmål, tilbakemeldinger eller har funnet feil i dataene? 
      Ta gjerne kontakt via nettstedene til NM janitsjar eller NM brass.
    </p>
  </section>
</div>

<style>
  .about-page {
    display: flex;
    flex-direction: column;
    gap: 2rem;
    max-width: 850px;
    margin: 0 auto;
    padding-bottom: 2rem;
  }

  .about-section {
    display: flex;
    flex-direction: column;
    gap: 0.85rem;
  }

  .about-section h2 {
    margin: 0;
    font-size: 1.75rem;
    color: var(--color-accent);
    font-weight: 700;
  }

  .about-section h3 {
    margin: 0;
    font-size: 1.35rem;
    color: var(--color-text-primary);
    font-weight: 600;
    margin-top: 0.5rem;
  }

  .about-section h4 {
    margin: 0.75rem 0 0.35rem 0;
    font-size: 1.1rem;
    color: var(--color-text-primary);
    font-weight: 600;
  }

  .about-section p {
    margin: 0;
    line-height: 1.7;
    color: var(--color-text-secondary);
    font-size: 0.95rem;
  }

  .about-section ul {
    margin: 0;
    padding-left: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .about-section li {
    line-height: 1.7;
    color: var(--color-text-secondary);
    font-size: 0.95rem;
  }

  .about-section li strong {
    color: var(--color-text-primary);
    font-weight: 600;
  }

  .about-section a {
    color: var(--color-accent);
    text-decoration: none;
    transition: color 0.18s ease;
  }

  .about-section a:hover {
    color: var(--color-accent-strong);
    text-decoration: underline;
  }

  .about-section a:focus-visible {
    outline: 2px solid var(--color-accent);
    outline-offset: 2px;
    border-radius: 2px;
  }

  .about-footer {
    margin-top: 1rem;
    padding-top: 1.5rem;
    border-top: 1px solid var(--color-border);
  }

  .about-footer p {
    font-style: italic;
    color: var(--color-text-muted);
  }

  .indicator-promote {
    background-color: rgba(16, 185, 129, 0.25);
    padding: 0.15rem 0.4rem;
    border-radius: 0.25rem;
    font-weight: 600;
    color: var(--color-text-primary);
  }

  .indicator-demote {
    background-color: rgba(239, 68, 68, 0.25);
    padding: 0.15rem 0.4rem;
    border-radius: 0.25rem;
    font-weight: 600;
    color: var(--color-text-primary);
  }

  @media (max-width: 640px) {
    .about-page {
      gap: 1.5rem;
      padding-bottom: 1.5rem;
    }

    .about-section h2 {
      font-size: 1.5rem;
    }

    .about-section h3 {
      font-size: 1.2rem;
    }

    .about-section h4 {
      font-size: 1rem;
    }

    .about-section p,
    .about-section li {
      font-size: 0.9rem;
    }
  }
</style>
