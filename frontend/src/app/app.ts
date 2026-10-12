import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

/** Componente raiz: solo muestra la pagina que indique el router. */
@Component({
  selector: 'app-root',
  imports: [RouterOutlet],
  template: '<router-outlet />',
})
export class App {}
