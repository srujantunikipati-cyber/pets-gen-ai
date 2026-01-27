// src/db/repository.ts
import { AppDataSource } from "../config/postgres";
import { EntityTarget, Repository, ObjectLiteral } from "typeorm";

export const getDBRepository = <T extends ObjectLiteral>(entity: EntityTarget<T>): Repository<T> => {
  return AppDataSource.getRepository<T>(entity);
};
