import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
} from "typeorm";

@Entity({ name: "master_login_type" })
export class MasterLoginType {
  
  @PrimaryGeneratedColumn("increment")
  id!: number; // sequential integer ID
  
  @Column({ type: "varchar", unique: true })
  type!: string;  // e.g. "google", "password", "facebook"

  @Column({ type: "varchar", nullable: true })
  createdBy?: string; // admin or system user id

  @CreateDateColumn({ type: "timestamp with time zone" })
  createdAt!: Date;
}
