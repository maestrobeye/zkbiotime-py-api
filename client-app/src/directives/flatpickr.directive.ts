import { Directive, ElementRef, AfterViewInit, OnDestroy, inject, input } from '@angular/core';
import flatpickr from 'flatpickr';
import { French } from 'flatpickr/dist/l10n/fr.js';

@Directive({
  selector: '[appFlatpickr]'
})
export class FlatpickrDirective implements AfterViewInit, OnDestroy {
  private el: ElementRef<HTMLInputElement> = inject(ElementRef);
  private instance: flatpickr.Instance | null = null;

  enableTime = input(true);
  // The 'T' needs to be escaped for flatpickr's formatter.
  dateFormat = input('Y-m-d\\TH:i'); 
  altInput = input(true);
  altFormat = input('j F Y à H:i');

  ngAfterViewInit() {
    this.instance = flatpickr(this.el.nativeElement, {
      enableTime: this.enableTime(),
      dateFormat: this.dateFormat(),
      altInput: this.altInput(),
      altFormat: this.altFormat(),
      locale: French,
      onChange: () => {
        // When flatpickr changes, dispatch an 'input' event on the original
        // element to notify ngModel of the change.
        const event = new Event('input', { bubbles: true });
        this.el.nativeElement.dispatchEvent(event);
      },
    });
  }

  ngOnDestroy() {
    this.instance?.destroy();
  }
}