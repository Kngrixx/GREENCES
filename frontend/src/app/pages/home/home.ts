import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterLink } from '@angular/router';

import { UMBRALES } from '../../core/config';
import { Icono, NombreIcono } from '../../shared/icono/icono';

/**
 * Home - Presenta GreenCES como propuesta de producto: que problema resuelve,
 * que variables vigila, como decide y como esta construido.
 */
@Component({
  selector: 'app-home',
  imports: [RouterLink, Icono],
  templateUrl: './home.html',
  styleUrl: './home.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Home {
  protected readonly u = UMBRALES;

  protected readonly variables: { icono: NombreIcono; clase: string; titulo: string; sensor: string; texto: string }[] = [
    {
      icono: 'termometro',
      clase: 'temperatura',
      titulo: 'Temperatura',
      sensor: 'Sensor HTU21D (I2C)',
      texto: 'Indica cuándo el ambiente se calienta. Define la intensidad del LED verde, la alarma roja y el ventilador.',
    },
    {
      icono: 'gota',
      clase: 'humedad',
      titulo: 'Humedad ambiente',
      sensor: 'Sensor HTU21D (I2C)',
      texto: 'Humedad relativa del aire en la zona de almacenamiento. Junto con la del sustrato, controla el LED blanco.',
    },
    {
      icono: 'brote',
      clase: 'suelo',
      titulo: 'Humedad del sustrato',
      sensor: 'Sonda YL-69 (analógica)',
      texto: 'Medida resistiva del sustrato, calibrada de 0 % (seco) a 100 % (sumergido).',
    },
  ];

  protected readonly pasos: { icono: NombreIcono; titulo: string; texto: string }[] = [
    {
      icono: 'chip',
      titulo: 'Sensa y decide',
      texto: 'El ESP32 mide cada 2 s, aplica las reglas de control y maneja los LEDs y el relé del ventilador sin detenerse (temporización con ticks, sin sleep).',
    },
    {
      icono: 'wifi',
      titulo: 'Transmite',
      texto: 'Con el sistema encendido envía un JSON por WiFi cada 15 s al servidor local (POST /api/lecturas).',
    },
    {
      icono: 'base-datos',
      titulo: 'Valida y guarda',
      texto: 'La API en Flask revisa cada dato y lo guarda en PostgreSQL. Las consultas están protegidas con login y token JWT.',
    },
    {
      icono: 'pantalla',
      titulo: 'Muestra',
      texto: 'Esta aplicación en Angular presenta el estado en tiempo real y el histórico con máximos, mínimos y la tendencia de temperatura.',
    },
  ];

  protected readonly hardware = [
    'Heltec WiFi LoRa 32 V3 (ESP32-S3)',
    'HTU21D: temperatura y humedad',
    'YL-69 + YL-38: humedad del sustrato',
    'Relé de 5 V + ventilador DC',
    'LED verde (PWM), rojo y blanco',
    'Pulsador de encendido/apagado',
  ];

  protected readonly tecnologia = ['MicroPython', 'Flask', 'SQLAlchemy', 'PostgreSQL', 'JWT', 'Angular'];
}
