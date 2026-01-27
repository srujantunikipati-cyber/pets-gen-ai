import { Entity, PrimaryGeneratedColumn, Column, Unique, ManyToOne, JoinColumn } from "typeorm";
import { ObjectType, Field, ID } from "type-graphql";
import { MasterLoginType } from "./MasterLoginType";

@ObjectType()
@Entity()
@Unique(["firebaseId"])
@Unique(["email"])
@Unique(["username"]) // ✅ new unique username
export class User {
  @Field(() => ID)
  @PrimaryGeneratedColumn("uuid")
  id!: string;

  @Field()
  @Column()
  firstName!: string;

  @Field()
  @Column()
  lastName!: string;

  @Field()
  @Column({ unique: true })
  email!: string;

  @Field()
  @Column({ unique: true })
  username!: string;

  @Field()
  @Column({ unique: true })
  firebaseId!: string;

  @Field()
  @Column()
  dob!: string;

  @Field()
  @Column()
  phoneNumber!: string;

  @Field()
  @Column({ default: false })
  isVerified!: boolean;

  @ManyToOne(() => MasterLoginType)
  @JoinColumn({ name: "loginTypeId" })
  loginType?: MasterLoginType;


@Column({ nullable: true })
  loginTypeId?: number;
}
