import { Entity, PrimaryGeneratedColumn, Column, OneToMany } from 'typeorm';
import { DividendEntity } from './DividendEntity';
import { FinancialDataEntity } from './FinancialDataEntity';

@Entity()
export class StockEntity {
  @PrimaryGeneratedColumn()
  id: number;

  @Column()
  ticker: string;

  @Column()
  companyName: string;

  @Column()
  sector: string;

  @OneToMany(() => DividendEntity, (dividend) => dividend.stock)
  dividends!: DividendEntity[];

  @OneToMany(() => FinancialDataEntity, (financialData) => financialData.stock)
  financialData!: FinancialDataEntity[];

  constructor() {
    this.id = 0;
    this.ticker = '';
    this.companyName = '';
    this.sector = '';
  }
}