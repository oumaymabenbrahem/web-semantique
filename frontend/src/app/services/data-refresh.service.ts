import { Injectable } from '@angular/core';
import { Subject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class DataRefreshService {
  private refreshSubject = new Subject<void>();
  
  // Observable que le dashboard peut écouter
  refreshData$ = this.refreshSubject.asObservable();

  // Méthode pour déclencher le rafraîchissement
  triggerRefresh() {
    this.refreshSubject.next();
  }
}
