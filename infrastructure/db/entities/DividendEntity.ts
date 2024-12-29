import { Entity, PrimaryGeneratedColumn, Column, ManyToOne } from 'typeorm';
import { StockEntity } from './StockEntity';

@Entity()
export class DividendEntity {
  @PrimaryGeneratedColumn()
  id: number;

  @Column()
  exDate: Date;

  @Column()
  payDate: Date;

  @Column('decimal', { precision: 10, scale: 2 })
  amount: number;

  @ManyToOne(() => StockEntity, (stock) => stock.dividends)
  stock: StockEntity;

  constructor() {
    this.id = 0;
    this.exDate = new Date();
    this.payDate = new Date();
    this.amount = 0;
    this.stock = new StockEntity();
  }
}