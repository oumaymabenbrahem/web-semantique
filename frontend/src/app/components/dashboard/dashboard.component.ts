import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subscription } from 'rxjs';
import { OntologyService, OntologyStats, Destination, Hebergement, Activite, Transport, Service, Nourriture, Equipement, Personne, Certification } from '../../services/ontology.service';
import { DataRefreshService } from '../../services/data-refresh.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css']
})
export class DashboardComponent implements OnInit, OnDestroy {
  stats: OntologyStats = { classes: 0, properties: 0, individuals: 0 };
  destinations: Destination[] = [];
  hebergements: Hebergement[] = [];
  activites: Activite[] = [];
  transports: Transport[] = [];
  services: Service[] = [];
  nourritures: Nourriture[] = [];
  equipements: Equipement[] = [];
  personnes: Personne[] = [];
  certifications: Certification[] = [];
  loading: boolean = true;
  apiStatus: string = 'Vérification...';
  
  private refreshSubscription?: Subscription;

  constructor(
    private ontologyService: OntologyService,
    private dataRefreshService: DataRefreshService
  ) { }

  ngOnInit(): void {
    this.checkApiHealth();
    this.loadData();
    
    // S'abonner aux événements de rafraîchissement
    this.refreshSubscription = this.dataRefreshService.refreshData$.subscribe(() => {
      console.log('🔄 Rafraîchissement des données du dashboard...');
      this.loadData();
    });
  }
  
  ngOnDestroy(): void {
    // Nettoyer la souscription
    if (this.refreshSubscription) {
      this.refreshSubscription.unsubscribe();
    }
  }

  checkApiHealth(): void {
    this.ontologyService.getHealth().subscribe({
      next: (response) => {
        this.apiStatus = 'Connectée ✓';
      },
      error: (err) => {
        this.apiStatus = 'Déconnectée ✗';
      }
    });
  }

  loadData(): void {
    this.loading = true;

    this.ontologyService.getStats().subscribe({
      next: (stats) => {
        this.stats = stats;
      },
      error: (err) => console.error('Erreur stats:', err)
    });

    this.ontologyService.getDestinations().subscribe({
      next: (destinations) => {
        this.destinations = destinations;
      },
      error: (err) => console.error('Erreur destinations:', err)
    });

    this.ontologyService.getHebergements().subscribe({
      next: (hebergements) => {
        this.hebergements = hebergements;
      },
      error: (err) => console.error('Erreur hébergements:', err)
    });

    this.ontologyService.getActivites().subscribe({
      next: (activites) => {
        this.activites = activites;
        this.loading = false;
      },
      error: (err) => {
        console.error('Erreur activités:', err);
        this.loading = false;
      }
    });

    this.ontologyService.getTransports().subscribe({
      next: (transports) => {
        this.transports = transports;
      },
      error: (err) => console.error('Erreur transports:', err)
    });

    this.ontologyService.getServices().subscribe({
      next: (services) => {
        this.services = services;
      },
      error: (err) => console.error('Erreur services:', err)
    });

    this.ontologyService.getNourritures().subscribe({
      next: (nourritures) => {
        this.nourritures = nourritures;
      },
      error: (err) => console.error('Erreur nourritures:', err)
    });

    this.ontologyService.getEquipements().subscribe({
      next: (equipements) => {
        this.equipements = equipements;
      },
      error: (err) => console.error('Erreur équipements:', err)
    });

    this.ontologyService.getPersonnes().subscribe({
      next: (personnes) => {
        this.personnes = personnes;
      },
      error: (err) => console.error('Erreur personnes:', err)
    });

    this.ontologyService.getCertifications().subscribe({
      next: (certifications) => {
        this.certifications = certifications;
      },
      error: (err) => console.error('Erreur certifications:', err)
    });
  }

  extractClassName(uri: string): string {
    const parts = uri.split('#');
    return parts.length > 1 ? parts[1] : uri;
  }
}
