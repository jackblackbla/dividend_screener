import { DataSource } from 'typeorm';
import { StockEntity } from '../db/entities/StockEntity';
import { DividendEntity } from '../db/entities/DividendEntity';
import { FinancialDataEntity } from '../db/entities/FinancialDataEntity';
import * as dotenv from 'dotenv';

dotenv.config();

export const AppDataSource = new DataSource({
  type: 'postgres',
  host: process.env.DB_HOST,
  port: +process.env.DB_PORT!,
  username: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  database: process.env.DB_NAME,
  entities: [StockEntity, DividendEntity, FinancialDataEntity],
  synchronize: false,
  logging: true,
});