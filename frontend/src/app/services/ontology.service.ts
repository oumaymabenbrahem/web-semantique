import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface OntologyStats {
  classes: number;
  properties: number;
  individuals: number;
}

export interface Destination {
  uri: string;
  nom: string | null;
  type: string | null;
}

export interface Hebergement {
  uri: string;
  nom: string | null;
  type: string | null;
  certification: string | null;
}

export interface Activite {
  uri: string;
  nom: string | null;
  duree: number | null;
  empreinte: number | null;
  type: string | null;
}

export interface Transport {
  uri: string;
  type: string | null;
  empreinte: number | null;
}

export interface Service {
  uri: string;
  nom: string | null;
  prix: number | null;
}

export interface Nourriture {
  uri: string;
  nom: string | null;
}

export interface Equipement {
  uri: string;
  nom: string | null;
}

export interface Personne {
  uri: string;
  nom: string | null;
  age: number | null;
}

export interface Certification {
  uri: string;
  nom: string | null;
  dateValidite: string | null;
}

export interface QueryResult {
  success: boolean;
  results: any[];
  count: number;
  question?: string;
  sparql?: string;
  error?: string;
}

@Injectable({
  providedIn: 'root'
})
export class OntologyService {
  // Backend avec CRUD sur le port 5000
  private apiUrl = 'http://localhost:5000/api';

  constructor(private http: HttpClient) { }

  getHealth(): Observable<any> {
    return this.http.get(`${this.apiUrl}/health`);
  }

  getStats(): Observable<OntologyStats> {
    return this.http.get<OntologyStats>(`${this.apiUrl}/ontology/stats`);
  }

  getDestinations(): Observable<Destination[]> {
    return this.http.get<Destination[]>(`${this.apiUrl}/destinations`);
  }

  getHebergements(): Observable<Hebergement[]> {
    return this.http.get<Hebergement[]>(`${this.apiUrl}/hebergements`);
  }

  getActivites(): Observable<Activite[]> {
    return this.http.get<Activite[]>(`${this.apiUrl}/activites`);
  }

  getTransports(): Observable<Transport[]> {
    return this.http.get<Transport[]>(`${this.apiUrl}/transports`);
  }

  getServices(): Observable<Service[]> {
    return this.http.get<Service[]>(`${this.apiUrl}/services`);
  }

  getNourritures(): Observable<Nourriture[]> {
    return this.http.get<Nourriture[]>(`${this.apiUrl}/nourritures`);
  }

  getEquipements(): Observable<Equipement[]> {
    return this.http.get<Equipement[]>(`${this.apiUrl}/equipements`);
  }

  getPersonnes(): Observable<Personne[]> {
    return this.http.get<Personne[]>(`${this.apiUrl}/personnes`);
  }

  getCertifications(): Observable<Certification[]> {
    return this.http.get<Certification[]>(`${this.apiUrl}/certifications`);
  }

  executeQuery(query: string): Observable<QueryResult> {
    return this.http.post<QueryResult>(`${this.apiUrl}/query`, { query });
  }

  askQuestion(question: string): Observable<QueryResult> {
    return this.http.post<QueryResult>(`${this.apiUrl}/nl-query`, { question });
  }
}
