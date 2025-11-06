import { Routes } from '@angular/router';
import { DashboardComponent } from './components/dashboard/dashboard.component';
import { QueryComponent } from './components/query/query.component';

export const routes: Routes = [
  { path: '', component: DashboardComponent },
  { path: 'dashboard', component: DashboardComponent },
  { path: 'query', component: QueryComponent },
  { path: '**', redirectTo: '' }
];
