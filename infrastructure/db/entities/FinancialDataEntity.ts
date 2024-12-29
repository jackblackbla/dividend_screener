import { Entity, PrimaryGeneratedColumn, Column, ManyToOne } from 'typeorm';
import { StockEntity } from './StockEntity';

@Entity()
export class FinancialDataEntity {
  @PrimaryGeneratedColumn()
  id: number;

  @Column()
  fiscalYear: number;

  @Column('decimal', { precision: 15, scale: 2 })
  revenue: number;

  @Column('decimal', { precision: 15, scale: 2 })
  netIncome: number;

  @ManyToOne(() => StockEntity, (stock) => stock.financialData)
  stock: StockEntity;

  constructor() {
    this.id = 0;
    this.fiscalYear = 0;
    this.revenue = 0;
    this.netIncome = 0;
    this.stock = new StockEntity();
  }
}