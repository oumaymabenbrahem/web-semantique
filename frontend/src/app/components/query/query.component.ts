import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { OntologyService, QueryResult } from '../../services/ontology.service';
import { DataRefreshService } from '../../services/data-refresh.service';

@Component({
  selector: 'app-query',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './query.component.html',
  styleUrls: ['./query.component.css']
})
export class QueryComponent implements OnInit {
  
  question: string = '';
  results: any[] = [];
  sparqlQuery: string = '';
  loading: boolean = false;
  error: string = '';
  successMessage: string = '';
  crudAction: string = ''; // 'create', 'update', 'delete', ou ''
  
  predefinedQuestions: string[] = [
    'Quelles sont toutes les destinations ?',
    'Quels hébergements ont une certification ?',
    'Quelles activités ont une faible empreinte carbone ?',
    'Quels sont les transports écologiques ?',
    'Quelles sont toutes les personnes ?'
  ];
  
  crudExamples: string[] = [
    '➕ Ajoute une personne [nom] qui a [age] ans',
    '✏️ Modifie l\'âge de [nom] à [nouveau_age] ans',
    '🗑️ Supprime la personne [nom]',
    '➕ Crée une destination [nom] dans le pays [pays]',
    '➕ Ajoute un service [nom] à [prix] euros'
  ];

  constructor(
    private ontologyService: OntologyService,
    private dataRefreshService: DataRefreshService
  ) { }

  ngOnInit(): void { }

  selectQuestion(q: string): void {
    this.question = q;
  }

  askQuestion(): void {
    if (!this.question.trim()) {
      this.error = 'Veuillez entrer une question';
      return;
    }

    this.loading = true;
    this.error = '';
    this.successMessage = '';
    this.results = [];
    this.sparqlQuery = '';
    this.crudAction = '';

    this.ontologyService.askQuestion(this.question).subscribe({
      next: (response: any) => {
        this.loading = false;
        if (response.success) {
          // Détecter si c'est une opération CRUD
          if (response.action) {
            this.crudAction = response.action;
            this.successMessage = response.message;
            
            // Notifier le dashboard pour rafraîchir les données
            setTimeout(() => {
              this.dataRefreshService.triggerRefresh();
            }, 500);
            
            // Afficher les détails de l'entité si disponibles
            if (response.entity) {
              this.results = [response.entity];
            }
          } else {
            // C'est une requête SELECT normale
            this.results = response.results;
            this.sparqlQuery = response.sparql || '';
          }
        } else {
          this.error = response.error || 'Erreur inconnue';
        }
      },
      error: (err) => {
        this.loading = false;
        this.error = err.error?.error || 'Erreur de connexion à l\'API';
        
        // Afficher la suggestion si disponible
        if (err.error?.suggestion) {
          this.error += '\n💡 ' + err.error.suggestion;
        }
      }
    });
  }

  getResultKeys(): string[] {
    if (this.results.length === 0) return [];
    return Object.keys(this.results[0]);
  }
  
  clearMessages(): void {
    this.error = '';
    this.successMessage = '';
    this.results = [];
    this.sparqlQuery = '';
  }
}
